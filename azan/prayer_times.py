import requests


ALADHAN_URL = "https://api.aladhan.com/v1/timingsByCity"

PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]


def fetch_prayer_times(city, country, method=1, school=1):
    params = {
        "city": city,
        "country": country,
        "method": method,
        "school": school,
    }
    resp = requests.get(ALADHAN_URL, params=params, timeout=10)
    resp.raise_for_status()

    timings = resp.json()["data"]["timings"]
    return {name: timings[name].split(" ")[0] for name in PRAYER_NAMES}
