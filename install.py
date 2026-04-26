#!/usr/bin/env python3
"""Azan Automation — Interactive Installer.

Idempotent: safe to rerun. Each step checks if already done and skips.
"""

import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azan import config, discovery, platform_utils as pf
from azan.scheduler import print_cron_preview, write_cron


def header(text):
    width = 50
    print(f"\n{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}")


def step(num, total, label):
    print(f"\nStep {num}/{total}: {label}")
    print("-" * 40)


def check_venv_packages():
    """Check if all required packages are importable in venv."""
    python = pf.get_venv_python()
    try:
        subprocess.run(
            [python, "-c", "import requests; import yaml; import catt"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    total_steps = 8

    header("Azan Automation Setup")

    # ── Step 0: Platform Detection ──────────────────────────────
    step(0, total_steps, "Platform Detection")
    plat = pf.detect_platform()
    print(f"  Platform : {plat['type']}")
    print(f"  Arch     : {plat['arch']}")
    print(f"  Pi       : {plat['is_pi']}")

    # ── Step 1: System Dependencies ─────────────────────────────
    step(1, total_steps, "System Dependencies")
    if pf.ensure_system_deps(plat):
        print("  System deps OK")
    else:
        print("  Cannot proceed without system dependencies.")
        sys.exit(1)

    # ── Step 2: Virtual Environment ─────────────────────────────
    step(2, total_steps, "Virtual Environment")
    if pf.venv_exists():
        print("  venv already exists")
    else:
        print("  Creating venv...")
        pf.create_venv()
        print("  venv created")

    # ── Step 3: Python Dependencies ─────────────────────────────
    step(3, total_steps, "Python Dependencies")
    if check_venv_packages():
        print("  All packages installed")
    else:
        print("  Installing packages...")
        python = pf.get_venv_python()
        flags = pf.pip_install_flags(plat)
        cmd = [python, "-m", "pip", "install", "-r",
               os.path.join(pf.project_root(), "requirements.txt")] + flags
        subprocess.run(cmd, check=True)
        print("  Packages installed")

    # ── Step 4: Location ────────────────────────────────────────
    step(4, total_steps, "Location")
    cfg = config.load_config()

    cfg["city"] = config.get_or_prompt(cfg, "city", "City", "Gurgaon")
    cfg["country"] = config.get_or_prompt(cfg, "country", "Country", "India")
    cfg["method"] = int(config.get_or_prompt(
        cfg, "method",
        "Calculation method (1=Karachi/Hanafi, 2=ISNA, 3=MWL)", "1"
    ))
    if cfg["method"] == 1:
        cfg["school"] = 1  # Hanafi for Karachi method
    else:
        school = config.get_or_prompt(
            cfg, "school",
            "School (0=Shafi, 1=Hanafi)", "0"
        )
        cfg["school"] = int(school)

    config.save_config(cfg)
    print(f"  Saved: {cfg['city']}, {cfg['country']} (method={cfg['method']})")

    # ── Step 5: Device Discovery ────────────────────────────────
    step(5, total_steps, "Google Home Device")
    cfg = config.load_config()

    if config.get(cfg, "device_name"):
        print(f"  Device already set: {cfg['device_name']}")
    else:
        print("  Scanning for Google Home devices...")
        catt = pf.get_venv_catt()
        devices = discovery.scan_chromecast_devices(catt)

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
            idx = int(choice) - 1 if choice.isdigit() else 0
            cfg["device_name"] = devices[idx][0]
            print(f"  Selected: {cfg['device_name']}")

        config.save_config(cfg)

    # ── Step 6: Home Assistant (Optional) ───────────────────────
    step(6, total_steps, "Home Assistant (optional)")
    cfg = config.load_config()

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
                choice = input(
                    f"  Select [1-{len(players) + 1}]: "
                ).strip()
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

            config.save_config(cfg)
        else:
            print("  TV control skipped")

    # ── Step 7: Audio Files ─────────────────────────────────────
    step(7, total_steps, "Audio Files")
    cfg = config.load_config()

    cfg["azan_file"] = config.get_or_prompt(
        cfg, "azan_file", "Default azan audio path", "audio/azan.mp3"
    )
    cfg["fajr_azan_file"] = config.get_or_prompt(
        cfg, "fajr_azan_file", "Fajr azan audio path", "audio/fajr_azan.mp3"
    )
    cfg["azan_duration"] = int(config.get_or_prompt(
        cfg, "azan_duration", "Azan duration in seconds", "136"
    ))
    cfg["fajr_azan_duration"] = int(config.get_or_prompt(
        cfg, "fajr_azan_duration", "Fajr azan duration in seconds", "150"
    ))
    cfg["volume"] = config.get_or_prompt(
        cfg, "volume", "Volume (0-100)", "100"
    )
    cfg["scan_before_minutes"] = int(config.get_or_prompt(
        cfg, "scan_before_minutes",
        "Minutes before prayer to scan device", "5"
    ))

    config.save_config(cfg)
    print("  Audio settings saved")

    # ── Step 8: Cron Setup ──────────────────────────────────────
    step(8, total_steps, "Cron Setup")

    python = pf.get_venv_python()
    root = pf.project_root()
    setup_cmd = f"{python} {root}/setup_cron.py"

    existing = _read_crontab()
    already_set = any("setup_cron.py" in line for line in existing)

    if already_set:
        print("  Cron entries already present")
    else:
        # Add @reboot + daily cron for setup_cron.py
        # Prayer-time crons are generated daily by setup_cron.py itself
        persistent = [
            f"@reboot sleep 60 && {setup_cmd}",
            f"0 0 * * * {setup_cmd}",
        ]
        filtered = [
            line for line in existing
            if "play_azan.py" not in line
            and "check_device.py" not in line
            and "setup_cron.py" not in line
        ]
        new_cron = "\n".join(filtered + persistent) + "\n"
        proc = subprocess.run(
            ["crontab", "-"], input=new_cron, text=True, capture_output=True,
        )
        if proc.returncode == 0:
            print("  Cron entries written")
        else:
            print(f"  ERROR writing crontab: {proc.stderr}")
            print("  You can add manually:")
            for line in persistent:
                print(f"    {line}")

    # ── Done ────────────────────────────────────────────────────
    header("Setup Complete!")

    print(f"""
  Config: {config.CONFIG_FILE}
  Log:    {os.path.join(root, cfg.get('log_file', 'azan.log'))}

  Next steps:
    1. Add your audio files to audio/ directory
    2. Run: {python} {root}/setup_cron.py
    3. Or just wait — cron will run setup_cron.py at midnight

  To reconfigure, run this installer again or edit config.yaml directly.
""")


def _read_crontab():
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True,
        )
        if result.returncode == 0:
            return [l for l in result.stdout.splitlines() if l.strip()]
    except FileNotFoundError:
        pass
    return []


if __name__ == "__main__":
    main()
