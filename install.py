#!/usr/bin/env python3
"""Azan Automation — Interactive Installer.

Idempotent: safe to rerun. Each step checks if already done and skips.
"""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azan.platform_utils import (
    detect_platform, ensure_system_deps, create_venv,
    get_venv_python, get_venv_catt, pip_install_flags, project_root,
)


def header(text):
    print(f"\n{'=' * 50}")
    print(f"  {text}")
    print(f"{'=' * 50}")


def step(num, total, label):
    print(f"\nStep {num}/{total}: {label}")
    print("-" * 40)


def check_venv_packages():
    python = get_venv_python()
    try:
        subprocess.run(
            [python, "-c", "import requests; import yaml; import catt"],
            capture_output=True, check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    total_steps = 8
    root = project_root()

    header("Azan Automation Setup")

    step(0, total_steps, "Platform Detection")
    plat = detect_platform()
    print(f"  Platform : {plat['type']}")
    print(f"  Arch     : {plat['arch']}")
    print(f"  Pi       : {plat['is_pi']}")

    step(1, total_steps, "System Dependencies")
    if ensure_system_deps(plat):
        print("  System deps OK")
    else:
        print("  Cannot proceed without system dependencies.")
        sys.exit(1)

    step(2, total_steps, "Virtual Environment")
    create_venv()
    print("  venv ready")

    step(3, total_steps, "Python Dependencies")
    if check_venv_packages():
        print("  All packages installed")
    else:
        print("  Installing packages...")
        python = get_venv_python()
        flags = pip_install_flags(plat)
        subprocess.run(
            [python, "-m", "pip", "install", "-r",
             os.path.join(root, "requirements.txt")] + flags,
            check=True,
        )
        print("  Packages installed")

    import glob
    site_packages = glob.glob(os.path.join(root, "venv", "lib", "*", "site-packages"))
    for sp in site_packages:
        if sp not in sys.path:
            sys.path.insert(0, sp)

    from azan import config, discovery, welcome
    from azan.scheduler import write_cron

    cfg = config.load_config()

    step(4, total_steps, "Location")
    print("  Coordinates come from the mosque website so times match exactly.")
    while True:
        try:
            cfg["latitude"] = float(config.get_or_prompt(cfg, "latitude", "Latitude"))
            cfg["longitude"] = float(config.get_or_prompt(cfg, "longitude", "Longitude"))
            break
        except ValueError:
            print("  Latitude/longitude must be numbers (e.g. 42.3601, -71.0589). Try again.")
            cfg.pop("latitude", None)
            cfg.pop("longitude", None)

    # City/country is only the fallback when no coordinates are set.
    cfg["city"] = cfg.get("city") or config.DEFAULTS["city"]
    cfg["country"] = cfg.get("country") or config.DEFAULTS["country"]

    cfg["method"] = int(config.get_or_prompt(
        cfg, "method",
        "Calculation method (2=ISNA, 3=MWL, 1=Karachi)",
    ))
    if cfg["method"] == 1:
        cfg["school"] = 1
    else:
        cfg["school"] = int(config.get_or_prompt(cfg, "school", "School (0=Shafi, 1=Hanafi)"))

    print(f"  Saved: {cfg['latitude']}, {cfg['longitude']} (method={cfg['method']})")

    step(5, total_steps, "Google Home Device")
    if config.get(cfg, "device_name"):
        print(f"  Device already set: {cfg['device_name']}")
    else:
        print("  Scanning for Google Home devices...")
        devices = discovery.scan_chromecast_devices(get_venv_catt())

        if not devices:
            print("  No devices found. Make sure Google Home is on the same network.")
            device_name = input("  Enter device name manually (or Ctrl+C to quit): ").strip()
            if not device_name:
                print("  No device name provided. Exiting.")
                sys.exit(1)
            cfg["device_name"] = device_name
        elif len(devices) == 1:
            cfg["device_name"] = devices[0][0]
            print(f"  Found: {devices[0][0]} ({devices[0][1]})")
        else:
            print(f"  Found {len(devices)} device(s):")
            for i, (name, ip) in enumerate(devices, 1):
                print(f"    [{i}] {name} ({ip})")
            choice = input(f"  Select device [1-{len(devices)}]: ").strip()
            idx = max(0, min(int(choice) - 1, len(devices) - 1)) if choice.isdigit() else 0
            cfg["device_name"] = devices[idx][0]
            print(f"  Selected: {cfg['device_name']}")

    step(6, total_steps, "Home Assistant (optional)")
    if config.get(cfg, "tv_entity_id"):
        print(f"  TV already configured: {cfg['tv_entity_id']}")
    else:
        ha_url = input("  HA URL (Enter to skip TV control): ").strip()
        if ha_url:
            ha_token = input("  HA Token: ").strip()
            cfg["ha_url"] = ha_url
            cfg["ha_token"] = ha_token

            print("  Discovering media players...")
            players = discovery.discover_ha_media_players(ha_url, ha_token)

            if players:
                print(f"  Found {len(players)} media player(s):")
                for i, (name, eid) in enumerate(players, 1):
                    print(f"    [{i}] {name} ({eid})")
                print(f"    [{len(players) + 1}] Skip TV control")
                choice = input(f"  Select [1-{len(players) + 1}]: ").strip()
                idx = int(choice) - 1 if choice.isdigit() else len(players)
                if 0 <= idx < len(players):
                    cfg["tv_entity_id"] = players[idx][1]
                    print(f"  Selected: {players[idx][1]}")
                else:
                    print("  TV control skipped")
            else:
                entity = input("  Enter TV entity ID manually (Enter to skip): ").strip()
                if entity:
                    cfg["tv_entity_id"] = entity
                else:
                    print("  TV control skipped")
        else:
            print("  TV control skipped")

    step(7, total_steps, "Audio Files")
    print("  Place your azan MP3 files in the audio/ directory.")
    print("  (You can skip this now and add them later.)\n")

    for key, label in [("azan_file", "azan"), ("fajr_azan_file", "fajr azan")]:
        default = config.get(cfg, key)
        full_path = os.path.join(root, default)
        if os.path.isfile(full_path):
            print(f"  Found: {default}")
        else:
            print(f"  Missing: {default}")
            custom = input(f"  Path to {label} MP3 (Enter to keep default): ").strip()
            if custom:
                cfg[key] = custom

    cfg["azan_duration"] = int(config.get_or_prompt(cfg, "azan_duration", "Azan duration in seconds"))
    cfg["fajr_azan_duration"] = int(config.get_or_prompt(cfg, "fajr_azan_duration", "Fajr azan duration in seconds"))
    cfg["volume"] = config.get_or_prompt(cfg, "volume", "Volume (0-100)")
    cfg["scan_before_minutes"] = int(config.get_or_prompt(cfg, "scan_before_minutes", "Minutes before prayer to scan device"))

    config.save_config(cfg)
    print("  Audio settings saved")

    step(8, total_steps, "Cron Setup")
    write_cron([], get_venv_python(), root)
    print("  Cron entries written")

    header("Setup Complete!")

    python = get_venv_python()
    print(f"""
  Config: {config.CONFIG_FILE}
  Log:    {os.path.join(root, config.get(cfg, 'log_file'))}

  Next steps:
    1. Add your audio files to audio/ directory
    2. Run: {python} {root}/setup_cron.py
    3. Or just wait — cron will run setup_cron.py at midnight

  To reconfigure, run this installer again or edit config.yaml directly.
""")

    print("Playing welcome message on your speaker...")
    try:
        welcome.play_welcome(get_venv_catt(), config.get(cfg, "device_name"))
        print("Welcome to Azan Automation!")
    except Exception:
        print("(Welcome message skipped — speaker not available)")


if __name__ == "__main__":
    main()
