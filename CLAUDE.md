# Azan Automation

Automated prayer time (Azan) player for Google Home / Chromecast devices on Raspberry Pi Zero 2 W.

## Project Structure

```
azan-automation/
├── azan/               # Core Python package
│   ├── __init__.py     # log() function with timestamps
│   ├── config.py       # config.yaml loader
│   ├── discovery.py    # catt scan wrapper
│   ├── player.py       # azan playback via catt
│   ├── scheduler.py    # prayer time API + cron setup
│   └── tv_control.py   # Home Assistant TV pause/resume
├── audio/              # Azan MP3 files
├── check_device.py     # Scan Google Home, reboot if not found
├── play_azan.py        # Main playback script (cron target)
├── setup_cron.py       # Fetch prayer times, update cron
├── install.py          # Interactive installer
├── setup.sh            # First-time setup
├── setup-pi.sh        # Pi one-shot setup (for fresh re-flashes)
├── wifi-logger.sh      # WiFi event logger (NM dispatcher)
└── config.yaml        # Runtime config (created by installer)
```

## Common Commands

### Pi Access
```bash
ssh raspi@10.147.18.185                    # ZeroTier (may be flaky)
ssh raspi@192.168.1.5                      # Local WiFi IP
rpi-connect ssh raspi                      # rpi-connect (backup)
```

### Logs
```bash
ssh raspi@10.147.18.185 "tail -30 ~/azan-automation/azan.log"
ssh raspi@10.147.18.185 "tail -30 ~/azan-automation/wifi.log"
```

### Azan Testing (no azan plays during testing)
```bash
ssh raspi@10.147.18.185 "venv/bin/python ~/azan-automation/check_device.py"
ssh raspi@10.147.18.185 "venv/bin/python ~/azan-automation/setup_cron.py --dry-run"
ssh raspi@10.147.18.185 "crontab -l"
```

### Pi Health
```bash
ssh raspi@10.147.18.185 "uptime && vcgencmd get_throttled"
ssh raspi@10.147.18.185 "free -h && df -h /"
```

### Cron (runs on Pi)
- `7,13,54,20 * * *` — check_device.py (5 min before each prayer)
- `12,18,59,25 * * *` — play_azan.py (at prayer time)
- `@reboot` + `0 0 * * *` — setup_cron.py (update prayer times)

## Gotchas

### Google Home Deep Sleep
Google Home falls into deep sleep between check (4:07) and play (4:12). `catt scan` works (mDNS) but `catt cast` fails (needs TCP). The 5-minute gap allows deep sleep. Acceptable trade-off since check_device.py handles reboot if scan fails.

### SD Card Protection (Pi Zero 2 W)
- `/tmp`, `/var/log` → tmpfs (RAM, wiped on reboot)
- journald → volatile mode (50MB max, 1-day retention)
- logrotate → weekly, keep 1
- **Sudden power loss is safe** — no writes to SD card during normal operation

### WiFi Drops
Pi Zero 2 W (BCM43430) drops WiFi every 30-60 seconds. ZeroTier becomes unreachable; reconnects automatically. rpi-connect is backup access.

### Prayer Times API (must match the mosque website)
`azan/prayer_times.py` hits Aladhan with the exact parameters baked into the mosque's website (`zamongajumath.com`, file `abic.js`): fixed coordinates `42.3601, -71.0589`, `method=2` (ISNA), `school=1` (Hanafi), and the `DD-MM-YYYY` date in the path. Do **not** switch to `timingsByCity` for the main path — that's only a fallback when coordinates are blanked out. Changing any of these makes the speakers drift from the website and the masjid TVs.

### Cron % Escaping
Never use `%` in cron commands — it's interpreted as newline. Use Python log() timestamps instead.

### Full Paths in NetworkManager Dispatcher
Scripts in `/etc/NetworkManager/dispatcher.d/` have limited PATH. Use full paths: `/usr/bin/date`, `/usr/bin/nmcli`, `/usr/bin/head`, etc.

### SSH Key Location
Always use `/home/raspi/.ssh/`, never `~/.ssh/` — `~` expands to `/root` under sudo.

## Pi Setup (setup-pi.sh)
For fresh Pi re-flashes, run `setup-pi.sh` which handles:
- WiFi power save disabled
- Sleep/suspend masked
- HDMI blanking disabled
- tmpfs for /tmp, /var/log
- journald volatile mode
- rpi-connect auto-restart
- ZeroTier install + join
- SSH key added
- azan-automation installer launched

After setup: authorize ZeroTier device at my.zerotier.com

## Google Home at 192.168.1.17
Device name configured in config.yaml. IP may vary; use catt scan to find.
