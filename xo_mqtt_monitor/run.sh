#!/usr/bin/env bash

# Použití 'bashio' pro snadné čtení konfigurace.
# Add-ony v HA defaultně obsahují bashio knihovnu.

# Funkce, která přečte hodnotu z /data/options.json a nastaví ji jako proměnnou prostředí.
# To je nejlepší způsob, jak přenést konfiguraci do Python skriptu.
export XO_URL=$(bashio::config 'xo_url')
export XO_USER=$(bashio::config 'xo_user')
export XO_PASS=$(bashio::config 'xo_pass')
export HOST_UUID=$(bashio::config 'host_uuid')

export MQTT_BROKER=$(bashio::config 'mqtt_broker')
export MQTT_PORT=$(bashio::config 'mqtt_port')
export MQTT_USER=$(bashio::config 'mqtt_user')
export MQTT_PASS=$(bashio::config 'mqtt_pass')
export BASE_TOPIC=$(bashio::config 'base_topic')
export INTERVAL=$(bashio::config 'interval')

echo "Spouštím XCP-ng/XO MQTT Monitor s načtenou konfigurací..."

# Spuštění Python skriptu
# Python skript nyní čte tyto exportované proměnné (viz bod 3)
exec python3 /xo_mqtt_monitor.py
