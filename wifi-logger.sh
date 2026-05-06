#!/bin/bash
LOG="/home/raspi/azan-automation/wifi.log"
INTERFACE="$1"
EVENT="$2"

if [ "$INTERFACE" != "wlan0" ]; then
    exit 0
fi

TIMESTAMP=$(/usr/bin/date '+%Y-%m-%d %H:%M:%S')

case "$EVENT" in
    up)
        SSID=$(/usr/bin/nmcli -t -f SSID dev wifi list 2>/dev/null | /usr/bin/head -1)
        IP=$(/usr/bin/ip -4 addr show wlan0 2>/dev/null | /usr/bin/grep inet | /usr/bin/awk '{print $2}')
        /usr/bin/logger -t wifi-logger "WiFi UP — SSID: $SSID — IP: $IP"
        echo "[$TIMESTAMP] WiFi UP — SSID: $SSID — IP: $IP" >> "$LOG"
        ;;
    down)
        /usr/bin/logger -t wifi-logger "WiFi DOWN"
        echo "[$TIMESTAMP] WiFi DOWN" >> "$LOG"
        ;;
    *)
        echo "[$TIMESTAMP] WiFi event: $EVENT" >> "$LOG"
        ;;
esac

# Keep only last 500 lines
/usr/bin/tail -500 "$LOG" > "$LOG.tmp" && /bin/mv "$LOG.tmp" "$LOG"
