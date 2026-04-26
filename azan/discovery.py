import subprocess
import sys

import requests


def scan_chromecast_devices(catt_path):
    """Scan for Chromecast/Google Home devices on the local network.

    Args:
        catt_path: Absolute path to the catt binary.

    Returns:
        list of (name, ip) tuples.
    """
    try:
        result = subprocess.run(
            [catt_path, "scan"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        print(f"ERROR: catt not found at {catt_path}")
        return []

    devices = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("Scanning"):
            continue
        # catt scan output format: "device_name - ip_address"
        if " - " in line:
            name, ip = line.split(" - ", 1)
            devices.append((name.strip(), ip.strip()))
    return devices


def discover_ha_media_players(ha_url, ha_token):
    """Discover media_player entities from Home Assistant.

    Args:
        ha_url: HA base URL (e.g. "http://localhost:8123")
        ha_token: HA long-lived access token

    Returns:
        list of (display_name, entity_id) tuples
    """
    try:
        resp = requests.get(
            f"{ha_url}/api/states",
            headers={
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"  Could not connect to Home Assistant: {e}")
        return []

    players = []
    for entity in resp.json():
        entity_id = entity.get("entity_id", "")
        if entity_id.startswith("media_player."):
            attrs = entity.get("attributes", {})
            friendly = attrs.get("friendly_name", entity_id)
            players.append((friendly, entity_id))
    return players
