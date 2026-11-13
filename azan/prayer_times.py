"""Prayer times from the Aladhan API.

The mosque's website (zamongajumath.com) calculates its athan times with
Aladhan using a fixed set of parameters. We send the exact same parameters
here so the speakers at the mosque play azan at the same minute the website
(and the masjid TVs) display:

    https://api.aladhan.com/v1/timings/DD-MM-YYYY
        ?latitude=42.3601&longitude=-71.0589&method=2&school=1

Coordinates take priority. City/country is kept as a fallback for setups that
have no coordinates configured.
"""

from datetime import datetime

import requests

ALADHAN_BASE = "https://api.aladhan.com/v1"
TIMINGS_URL = f"{ALADHAN_BASE}/timings"
TIMINGS_BY_CITY_URL = f"{ALADHAN_BASE}/timingsByCity"

# ABIC — Allston Brighton Islamic Center.
# Locked to the values baked into the mosque's website so every screen agrees.
MOSQUE_LATITUDE = 42.3601
MOSQUE_LONGITUDE = -71.0589
MOSQUE_METHOD = 2   # 2 = Islamic Society of North America (ISNA)
MOSQUE_SCHOOL = 1   # 1 = Hanafi (Asr)

PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]


def _has(value):
    """True when a config value is actually set (not None / empty string)."""
    return value is not None and str(value).strip() != ""


def _format_date(day=None):
    """Return the date in the DD-MM-YYYY form Aladhan expects in the path."""
    if day is None:
        day = datetime.now()
    if isinstance(day, str):
        return day
    return day.strftime("%d-%m-%Y")


def _clean_timings(timings):
    """Keep the five prayers, dropping Aladhan's timezone suffix / N/A values."""
    times = {}
    for name in PRAYER_NAMES:
        value = (timings.get(name) or "").split(" ")[0].strip()
        if value and value.upper() != "N/A":
            times[name] = value
    return times


def _fetch(url, params):
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return _clean_timings(resp.json()["data"]["timings"])


def fetch_prayer_times(latitude=None, longitude=None, method=MOSQUE_METHOD,
                       school=MOSQUE_SCHOOL, city=None, country=None, date=None):
    """Fetch prayer times for a location.

    Coordinates win when both latitude and longitude are given (this is the
    path the mosque website uses). Otherwise falls back to city/country.
    """
    if _has(latitude) and _has(longitude):
        return _fetch(TIMINGS_URL + "/" + _format_date(date), {
            "latitude": latitude,
            "longitude": longitude,
            "method": method,
            "school": school,
        })

    if not _has(city) or not _has(country):
        raise ValueError(
            "No location configured: set latitude/longitude (or city/country) "
            "in config.yaml."
        )

    return _fetch(TIMINGS_BY_CITY_URL, {
        "city": city,
        "country": country,
        "method": method,
        "school": school,
    })


def fetch_prayer_times_from_config(cfg, date=None):
    """Fetch prayer times using a loaded config.yaml dict.

    Uses coordinates when configured, otherwise the city/country fallback.
    """
    from azan import config

    return fetch_prayer_times(
        latitude=config.get(cfg, "latitude"),
        longitude=config.get(cfg, "longitude"),
        method=int(config.get(cfg, "method", MOSQUE_METHOD)),
        school=int(config.get(cfg, "school", MOSQUE_SCHOOL)),
        city=config.get(cfg, "city"),
        country=config.get(cfg, "country"),
        date=date,
    )
