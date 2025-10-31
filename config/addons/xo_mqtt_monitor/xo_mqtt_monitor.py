import os
import requests
import paho.mqtt.client as mqtt
import time
import json
import logging

# --- NAČTENÍ NASTAVENÍ Z PROSTŘEDÍ (PŘEDANÉ Z run.sh/config.json) ---
# Tyto proměnné jsou definovány v config.json a předány do kontejneru
try:
    XO_URL = os.environ.get("XO_URL")
    XO_USER = os.environ.get("XO_USER")
    XO_PASS = os.environ.get("XO_PASS")
    HOST_UUID = os.environ.get("HOST_UUID")

    MQTT_BROKER = os.environ.get("MQTT_BROKER")
    MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
    MQTT_USER = os.environ.get("MQTT_USER")
    MQTT_PASS = os.environ.get("MQTT_PASS")
    BASE_TOPIC = os.environ.get("BASE_TOPIC")
    INTERVAL = int(os.environ.get("INTERVAL", 30))

except (TypeError, ValueError) as e:
    # Zastaví skript, pokud chybí kritické proměnné
    print(f"Chyba konfigurace: Některá proměnná prostředí chybí nebo má špatný formát. {e}")
    exit(1)


# --- Konfigurace logování ---
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Globální proměnné ---
xo_session_id = None
mqtt_client = None

def get_xo_session(url, user, password):
    """Přihlásí se k XO API a vrátí token (session ID)."""
    global xo_session_id
    logging.info("Pokouším se získat nový XO token...")
    login_url = f"{url.rstrip('/')}/api/v0/session/login"
    
    try:
        response = requests.post(
            login_url,
            json={"email": user, "password": password},
            # Použijte verify=True, pokud máte platný HTTPS certifikát.
            # Pro testování v labu se často používá False.
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        
        # Získání a uložení session ID z hlavičky Set-Cookie
        cookie_header = response.headers.get("Set-Cookie", "")
        if "xen-orchestra=" in cookie_header:
            xo_session_id = cookie_header.split("xen-orchestra=")[1].split(";")[0]
            logging.info("XO token úspěšně získán.")
            return xo_session_id
        else:
            logging.error("XO nevrátilo platný 'xen-orchestra' token v hlavičce.")
            xo_session_id = None
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Chyba při přihlašování k XO na {login_url}: {e}")
        xo_session_id = None
        return None

def fetch_host_metrics(url, session_id, host_uuid):
    """Získá aktuální metriky hostitele XCP-ng."""
    headers = {"Cookie": f"xen-orchestra={session_id}"}
    metrics_url = f"{url.rstrip('/')}/api/v0/hosts/{host_uuid}"
    
    try:
        response = requests.get(
            metrics_url,
            headers=headers,
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        # --- PARSOVÁNÍ METRIK Z XO JSON ---
        # Poznámka: Konkrétní klíče (PCPU_utilization_avg, memory_used, atd.) 
        # se mohou mírně lišit v závislosti na verzi XO/XCP-ng.
        
        memory_used_bytes = data.get("memory_used", 0)
        memory_total_bytes = data.get("memory_total", 1) # Prevence dělení nulou

        metrics = {
            # CPU je v průměru 0-1. Přepočet na procenta.
            "cpu_usage_percent": data.get("PCPU_utilization_avg", 0) * 100,
            
            # Paměť
            "memory_usage_percent": (memory_used_bytes / memory_total_bytes) * 100,
            "memory_used_gb": memory_used_bytes / (1024**3),
            "memory_total_gb": memory_total_bytes / (1024**3),
            
            # Síťový provoz (network_rx/tx jsou v bytech za sekundu). Přepočet na Mbps.
            "network_rx_mbps": data.get("network_rx", 0) / (1024**2) * 8,
            "network_tx_mbps": data.get("network_tx", 0) / (1024**2) * 8
        }
        return metrics

    except requests.exceptions.HTTPError as e:
        if response.status_code in [401, 403]:
            logging.warning("XO Token vypršel nebo je neplatný. Signalizuji obnovení.")
            return False 
        logging.error(f"Chyba HTTP při získávání metrik z {metrics_url}: {response.status_code} - {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Chyba při komunikaci s XO API: {e}")
        return None

def publish_mqtt(topic, payload):
    """Publikuje data na MQTT broker."""
    if mqtt_client:
        # Použijeme qos=1 pro zaručené doručení
        mqtt_client.publish(topic, str(payload), qos=1, retain=False)
    else:
        logging.warning("MQTT klient není připojen. Nelze publikovat data.")

def setup_mqtt():
    """Inicializuje a připojí MQTT klienta."""
    global mqtt_client
    
    mqtt_client = mqtt.Client(client_id=f"xo_monitor_{os.getpid()}")
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    # Nastavení on_connect callbacku pro logování úspěchu
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("MQTT klient připojen k brokeru.")
        else:
            logging.error(f"MQTT připojení selhalo s kódem {rc}")
            
    mqtt_client.on_connect = on_connect
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start() 
    except Exception as e:
        logging.error(f"Kritická chyba při připojení k MQTT brokeru: {e}")

def main():
    """Hlavní smyčka."""
    global xo_session_id
    setup_mqtt()
    
    # Úvodní získání tokenu (je nutné pro první dotaz)
    if not get_xo_session(XO_URL, XO_USER, XO_PASS):
        logging.error("Počáteční připojení k XO selhalo. Opakuji za 60s.")
        time.sleep(60) 
        if not get_xo_session(XO_URL, XO_USER, XO_PASS):
            logging.error("Opakované připojení selhalo, ukončuji skript.")
            mqtt_client.loop_stop()
            return

    while True:
        metrics = fetch_host_metrics(XO_URL, xo_session_id, HOST_UUID)
        
        if metrics is False:
            # Token vypršel (HTTP 401/403). Zkusíme získat nový token.
            get_xo_session(XO_URL, XO_USER, XO_PASS)
            # Pokračujeme smyčkou a zkusíme získat metriky znovu.
            time.sleep(1) 
            continue 
        
        elif metrics:
            # Metriky získány, publikujeme je
            for key, value in metrics.items():
                topic = f"{BASE_TOPIC}/{key}"
                # Publikujeme hodnotu zaokrouhlenou na 2 desetinná místa
                publish_mqtt(topic, round(value, 2))
            
            logging.info(f"Metriky úspěšně publikovány. Další dotaz za {INTERVAL}s.")
        
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
