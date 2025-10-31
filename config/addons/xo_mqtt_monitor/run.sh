#!/usr/bin/env bash

# Skript pro spuštění add-onu.

# PŘEDÁNÍ KONFIGURAČNÍCH PROMĚNNÝCH do ENV (z config.json)
# Tyto proměnné jsou automaticky dostupné v bashu jako $XO_URL, atd.

# Spuštění Python skriptu s načtenými proměnnými
# Zajišťuje, že veškerá konfigurace je v bezpečném prostředí a není v Python kódu
python3 /xo_mqtt_monitor.py
