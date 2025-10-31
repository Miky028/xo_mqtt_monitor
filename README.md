1. Struktura adresářů 📁
Musíte vytvořit následující adresářovou strukturu ve složce doplňků Home Assistantu (nebo ve vašem vlastním repozitáři doplňků na GitHubu/jinde):

/config/
└── addons/
    └── xo_mqtt_monitor/       <-- Kořenová složka Add-onu
        ├── Dockerfile         <-- Popis pro vytvoření Docker image
        ├── config.json        <-- Metadata a konfigurace Add-onu
        ├── run.sh             <-- Spouštěcí skript Add-onu
        └── xo_mqtt_monitor.py <-- Váš Python skript
2. Soubor config.json (Metadata Add-onu)
Tento soubor informuje Home Assistant o doplňku, a hlavně definuje konfigurační proměnné, které uživatel vyplní v UI.

JSON

{
  "name": "XCP-ng / XO MQTT Monitor",
  "version": "1.0.0",
  "slug": "xo_mqtt_monitor",
  "description": "Získává metriky z Xen Orchestra API a publikuje je do Home Assistantu přes MQTT.",
  "arch": ["amd64", "armhf", "armv7", "aarch64"],
  "startup": "before",
  "boot": "auto",
  "map": ["config:rw"],
  "options": {
    "xo_url": "http://192.168.1.100:80",
    "xo_user": "readonly_user",
    "xo_pass": "supersecret",
    "host_uuid": "fill_your_xcpng_host_uuid",
    "mqtt_broker": "core-mosquitto",
    "mqtt_port": 1883,
    "mqtt_user": "homeassistant",
    "mqtt_pass": "HA_MQTT_PASSWORD",
    "base_topic": "xcpng/host/main",
    "interval": 30
  },
  "schema": {
    "xo_url": "str",
    "xo_user": "str",
    "xo_pass": "str",
    "host_uuid": "str",
    "mqtt_broker": "str",
    "mqtt_port": "int",
    "mqtt_user": "str",
    "mqtt_pass": "str",
    "base_topic": "str",
    "interval": "int"
  },
  "host_network": true 
}
Důležité: Všimněte si, že jsme použili "host_network": true. To je často potřeba, pokud Docker kontejner potřebuje přímo komunikovat s jinými zařízeními v síti mimo Docker bridge (v tomto případě s XO serverem).

3. Soubor Dockerfile (Konstrukce kontejneru)
Tento soubor říká Dockeru, jak postavit kontejner. Použijeme základní Python image a nainstalujeme závislosti.

Dockerfile

# Používáme oficiální base image pro HA add-ony
FROM ghcr.io/home-assistant/base-python:3.12

# Instalace závislostí
RUN pip install requests paho-mqtt

# Zkopírování spouštěcího skriptu a hlavního Python skriptu do kontejneru
COPY run.sh /
COPY xo_mqtt_monitor.py /

# Nastavení práv
RUN chmod a+x /run.sh

# Spouštěcí příkaz (entrypoint)
ENTRYPOINT ["/run.sh"]
4. Soubor xo_mqtt_monitor.py (Váš Python skript)
POZOR: Musíte upravit původní Python skript tak, aby četl nastavení z proměnných prostředí, které mu předá run.sh (viz bod 5), nikoli z tvrdě zakódovaných hodnot!

Klíčové změny v Python skriptu:

Python

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
5. Soubor run.sh (Spouštěcí logika)
Tento bash skript se spustí jako první. Načte konfiguraci z config.json (kterou Supervizor automaticky převede na proměnné prostředí) a spustí Python skript.

Bash

#!/usr/bin/env bash

# Skript pro spuštění add-onu.

# PŘEDÁNÍ KONFIGURAČNÍCH PROMĚNNÝCH do ENV (z config.json)
# Tyto proměnné jsou automaticky dostupné v bashu jako $XO_URL, atd.

# Spuštění Python skriptu s načtenými proměnnými
# Zajišťuje, že veškerá konfigurace je v bezpečném prostředí a není v Python kódu
python3 /xo_mqtt_monitor.py
Další krok
Uložte všechny soubory do správné adresářové struktury.

Pokud používáte vlastní repozitář Add-onů, přidejte jej do Home Assistantu. Pokud to ukládáte lokálně, musí být v adresáři addons ve vašem konfiguračním adresáři HA.

V Home Assistantu (Supervizor/Doplňky) se objeví nový doplněk.

Přejděte do nastavení doplňku, vyplňte všechny parametry (XO URL, uživatelé, UUID atd.) a spusťte jej!
