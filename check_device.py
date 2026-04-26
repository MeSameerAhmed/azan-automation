#!/usr/bin/env python3
"""Check if Google Home device is reachable. Reboot if not found.

Called by cron a few minutes before each prayer time.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azan import config, discovery
from azan.platform_utils import get_venv_catt, detect_platform, reboot


def main():
    cfg = config.load_config()
    if not cfg:
        print("ERROR: config.yaml not found.")
        sys.exit(1)

    device_name = config.get(cfg, "device_name")
    catt_path = get_venv_catt()

    print(f"Scanning for {device_name}...")
    devices = discovery.scan_chromecast_devices(catt_path)

    found = any(name == device_name for name, _ in devices)

    if found:
        print(f"{device_name} is online.")
    else:
        print(f"{device_name} NOT found!")
        plat = detect_platform()
        if plat["is_pi"] or plat["type"] == "linux":
            print("Rebooting...")
            reboot()
        else:
            print("Reboot not supported on this platform.")


if __name__ == "__main__":
    main()
