# Azan Automation

Automated prayer time (Azan) player for Google Home / Chromecast devices.

Fetches daily prayer times from the [Aladhan API](https://aladhan.com/prayer-times-api) using the **same parameters as the mosque's website** (Allston Brighton Islamic Center — [zamongajumath.com](https://zamongajumath.com)), casts Azan audio to your Google Home at each prayer time, and optionally pauses/resumes your TV via Home Assistant.

**Works on:** Raspberry Pi (Zero 2 W, 3, 4, 5), Linux, macOS

## Quick Start

No prerequisites — just run:

```bash
git clone https://github.com/YOUR_USERNAME/azan-automation.git
cd azan-automation
./setup.sh
```

`setup.sh` installs Python 3 if missing, then launches the interactive installer.

The installer will guide you through:

1. **System deps** — installs `python3-venv` etc. on Pi/Linux
2. **Virtual env** — creates `venv/` with all Python packages
3. **Location** — latitude/longitude, prayer calculation method
4. **Device discovery** — scans for Google Home devices on your network
5. **Home Assistant** *(optional)* — pauses/resumes TV during Azan
6. **Audio files** — paths to your Azan MP3 files
7. **Cron setup** — schedules everything automatically

### Add Your Audio Files

Place your Azan MP3s in the `audio/` directory:

```
audio/azan.mp3        # Regular azan
audio/fajr_azan.mp3   # Fajr azan (different recitation)
```

Set the duration (in seconds) in `config.yaml` to match your audio files (+ a few seconds buffer).

## How It Works

```
Daily @ Midnight + @Reboot
        │
        ▼
  setup_cron.py                ← Fetches today's prayer times from API
        │
        ▼
  Cron Updated                 ← 10 jobs: 5 device checks + 5 azan plays
        │
   ┌────┴──────────────────────────────────────┐
   │                                            │
   ▼  (5 min before prayer)                    ▼  (at prayer time)
  check_device.py            play_azan.py
  Scans for Google Home      Pauses TV → Plays Azan → Resumes TV
  Reboots Pi if not found
```

## Configuration

Config is stored in `config.yaml` (created by installer or manually from `config.yaml.example`):

| Setting | Default | Description |
|---------|---------|-------------|
| `latitude` | 42.3601 | Latitude for prayer times (mosque default) |
| `longitude` | -71.0589 | Longitude for prayer times (mosque default) |
| `method` | 2 | Prayer calculation method (see below) |
| `school` | 1 | 0=Shafi, 1=Hanafi |
| `city` | Boston | Fallback city — only used if coordinates are empty |
| `country` | United States | Fallback country — only used if coordinates are empty |
| `device_name` | — | Google Home device name |
| `volume` | 100 | Volume level (0-100) |
| `azan_file` | audio/azan.mp3 | Path to regular azan audio |
| `fajr_azan_file` | audio/fajr_azan.mp3 | Path to Fajr azan audio |
| `scan_before_minutes` | 5 | Minutes before prayer to check device |
| `ha_url` | — | Home Assistant URL (empty = skip TV control) |
| `ha_token` | — | HA long-lived access token |
| `tv_entity_id` | — | HA media_player entity for TV |

### Prayer Times API

Times are fetched from Aladhan with the exact parameters the mosque website uses:

```
https://api.aladhan.com/v1/timings/DD-MM-YYYY?latitude=42.3601&longitude=-71.0589&method=2&school=1
```

| Parameter | Value | Why |
|-----------|-------|-----|
| `latitude` / `longitude` | 42.3601 / -71.0589 | Baked into the website's `abic.js` — every screen shows identical athan times |
| `method` | 2 (ISNA) | The mosque's locked calculation method |
| `school` | 1 (Hanafi) | The mosque's locked Asr calculation |

Change `latitude`/`longitude` in `config.yaml` if you ever need a different location. If you blank both out, the code falls back to `city`/`country` via Aladhan's `timingsByCity` endpoint.

### Prayer Calculation Methods

| ID | Method |
|----|--------|
| 1 | University of Islamic Sciences, Karachi |
| 2 | Islamic Society of North America (ISNA) |
| 3 | Muslim World League |
| 4 | Umm Al-Qura University, Makkah |
| 5 | Egyptian General Authority of Survey |
| 7 | Institute of Geophysics, University of Tehran |

## Manual Commands

```bash
# Reconfigure
python3 install.py

# Fetch today's prayer times and update cron
python3 setup_cron.py

# Preview cron without writing
python3 setup_cron.py --dry-run

# Play azan manually
venv/bin/python play_azan.py 100
venv/bin/python play_azan.py 100 fajr

# Check device connectivity
venv/bin/python check_device.py
```

## Requirements

- **None** — `setup.sh` installs everything (Python 3, venv, pip packages)
- A Google Home / Chromecast device on the same network
- *(Optional)* Home Assistant running locally for TV control

## Platform Notes

- **Raspberry Pi Zero 2 W**: Fully supported. Uses `--no-cache-dir` for pip to save disk space. If the Google Home is unreachable before prayer time, the Pi reboots automatically.
- **Raspberry Pi 3/4/5**: Recommended. Best performance.
- **Linux desktop/server**: Works. Uses cron for scheduling.
- **macOS**: Works for development/testing. Reboot on device failure is skipped.

## License

MIT
