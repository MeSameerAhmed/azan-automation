#!/usr/bin/env python3
"""Play azan on Google Home. Called by cron at prayer time.

Usage: python3 play_azan.py <volume> [fajr]
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azan import config, player, tv_control
from azan.platform_utils import get_venv_catt


def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print("Usage: python3 play_azan.py <volume> [fajr]")
        sys.exit(1)

    volume = sys.argv[1]
    is_fajr = len(sys.argv) > 2 and sys.argv[2] == "fajr"

    cfg = config.load_config()
    if not cfg:
        print("ERROR: config.yaml not found. Run install.py first.")
        sys.exit(1)

    device_name = config.get(cfg, "device_name")
    azan_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        config.get(cfg, "fajr_azan_file" if is_fajr else "azan_file"),
    )
    catt_path = get_venv_catt()
    label = "Fajr " if is_fajr else ""

    # Pause TV if configured
    tv_was_active = False
    try:
        tv_was_active = tv_control.pause_tv(cfg)
    except Exception:
        pass  # never block azan

    # Play azan
    print(f"Playing {label}Azan on {device_name}...")
    success = player.play_azan(catt_path, device_name, azan_file, volume)

    if not success:
        if tv_was_active:
            try:
                tv_control.resume_tv(cfg)
            except Exception:
                pass
        sys.exit(1)

    # Wait for azan to finish
    duration = int(
        config.get(cfg, "fajr_azan_duration" if is_fajr else "azan_duration")
    )
    time.sleep(duration)

    print("Azan playback completed.")

    # Resume TV if it was active
    if tv_was_active:
        try:
            print("Resuming TV...")
            tv_control.resume_tv(cfg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
