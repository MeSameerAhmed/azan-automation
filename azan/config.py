import os
import sys

import yaml

from azan.platform_utils import project_root

CONFIG_FILE = os.path.join(project_root(), "config.yaml")
CONFIG_EXAMPLE = os.path.join(project_root(), "config.yaml.example")

DEFAULTS = {
    "city": "Gurgaon",
    "country": "India",
    "method": 1,
    "school": 1,
    "volume": "100",
    "scan_before_minutes": 5,
    "device_name": "",
    "azan_file": "audio/azan.mp3",
    "fajr_azan_file": "audio/fajr_azan.mp3",
    "azan_duration": 136,
    "fajr_azan_duration": 150,
    "log_file": "azan.log",
    "ha_url": "",
    "ha_token": "",
    "tv_entity_id": "",
}


def load_config():
    """Load config.yaml. Returns empty dict if not found."""
    try:
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def load_config_or_exit():
    """Load config or exit with error. Used by cron-triggered scripts."""
    cfg = load_config()
    if not cfg:
        print("ERROR: config.yaml not found. Run install.py first.")
        sys.exit(1)
    return cfg


def save_config(data):
    """Write config dict to config.yaml."""
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get(config, key, default=None):
    """Get a config value, falling back to DEFAULTS then provided default."""
    if config.get(key) is not None:
        return config[key]
    return DEFAULTS.get(key, default)


def get_or_prompt(config, key, prompt_text, default=None):
    """Return config value if set, otherwise prompt user interactively."""
    existing = config.get(key)
    if existing is not None and existing != "":
        return existing

    default_display = default if default is not None else DEFAULTS.get(key, "")
    prompt = f"  {prompt_text}"
    if default_display:
        prompt += f" [{default_display}]"
    prompt += ": "

    value = input(prompt).strip()
    if not value and default_display is not None:
        value = str(default_display)
    return value
