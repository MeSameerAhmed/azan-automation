#!/usr/bin/env python3
"""Play azan on Google Home. Called by cron at prayer time.

Usage: python3 play_azan.py <volume> [fajr]
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azan import config, player, tv_control
from azan.platform_utils import get_venv_catt, project_root


def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print("Usage: python3 play_azan.py <volume> [fajr]")
        sys.exit(1)

    volume = sys.argv[1]
    is_fajr = len(sys.argv) > 2 and sys.argv[2] == "fajr"

    cfg = config.load_config_or_exit()

    device_name = config.get(cfg, "device_name")
    prefix = "fajr_" if is_fajr else ""
    azan_file = os.path.join(
        project_root(), config.get(cfg, f"{prefix}azan_file"),
    )
    duration = int(config.get(cfg, f"{prefix}azan_duration"))

    tv_was_active = False
    try:
        tv_was_active = tv_control.pause_tv(cfg)
    except Exception:
        pass

    print(f"Playing {'Fajr ' if is_fajr else ''}Azan on {device_name}...")
    success = player.play_azan(get_venv_catt(), device_name, azan_file, volume)

    if not success:
        if tv_was_active:
            try:
                tv_control.resume_tv(cfg)
            except Exception:
                pass
        sys.exit(1)

    time.sleep(duration)

    print("Azan playback completed.")

    if tv_was_active:
        try:
            print("Resuming TV...")
            tv_control.resume_tv(cfg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
