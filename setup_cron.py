#!/usr/bin/env python3
"""Fetch today's prayer times and update cron jobs.

Called daily at midnight and @reboot by cron.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azan import config, prayer_times, scheduler


def main():
    dry_run = "--dry-run" in sys.argv

    cfg = config.load_config_or_exit()

    city = config.get(cfg, "city")
    country = config.get(cfg, "country")
    method = int(config.get(cfg, "method"))
    school = int(config.get(cfg, "school"))

    print(f"[{datetime.now()}] Fetching prayer times for {city}, {country}...")

    try:
        times = prayer_times.fetch_prayer_times(city, country, method, school)
    except Exception as e:
        print(f"ERROR fetching prayer times: {e}")
        sys.exit(1)

    print("\nToday's Prayer Schedule:")
    for name, t in times.items():
        print(f"  {name}: {t}")

    cron_lines = scheduler.generate_cron_jobs(cfg, times)

    if dry_run:
        scheduler.print_cron_preview(cron_lines)
    else:
        if scheduler.write_cron(cron_lines):
            print("\nCron updated successfully.")
        else:
            print("\nERROR updating cron.")
            sys.exit(1)


if __name__ == "__main__":
    main()
