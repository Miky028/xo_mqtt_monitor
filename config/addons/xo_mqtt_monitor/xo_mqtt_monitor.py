import os
# ... (ostatní importy zůstávají)

# --- NAČTENÍ NASTAVENÍ Z PROSTŘEDÍ ---
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

# ... zbytek kódu skriptu zůstává stejný, ale bez původních globálních proměnných
