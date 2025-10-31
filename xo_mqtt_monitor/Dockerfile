# Používáme oficiální base image pro HA add-ony
FROM ghcr.io/home-assistant/amd64-base:latest

# Instalace závislostí
RUN pip install requests paho-mqtt

# Zkopírování spouštěcího skriptu a hlavního Python skriptu do kontejneru
COPY run.sh /
COPY xo_mqtt_monitor.py /

# Nastavení práv
RUN chmod a+x /run.sh

# Spouštěcí příkaz (entrypoint)
ENTRYPOINT ["/run.sh"]
