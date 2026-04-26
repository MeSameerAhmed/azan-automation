import requests


ALADHAN_URL = "https://api.aladhan.com/v1/timingsByCity"

PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]


def fetch_prayer_times(city, country, method=1, school=1, retries=5, delay=10):
    """Fetch today's prayer times from the Aladhan API.

    Args:
        city: City name (e.g. "Gurgaon")
        country: Country name (e.g. "India")
        method: Calculation method (1=Karachi, 2=ISNA, 3=MWL, etc.)
        school: 0=Shafi, 1=Hanafi
        retries: Number of retries on network failure (for Pi boot)
        delay: Seconds between retries

    Returns:
        dict mapping prayer name to "HH:MM" string (24-hour)
    """
    import time

    params = {
        "city": city,
        "country": country,
        "method": method,
        "school": school,
    }

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(ALADHAN_URL, params=params, timeout=10)
            resp.raise_for_status()
            timings = resp.json()["data"]["timings"]
            return {name: timings[name].split(" ")[0] for name in PRAYER_NAMES}
        except Exception as e:
            last_error = e
            if attempt < retries:
                print(f"  Network error (attempt {attempt}/{retries}), retrying in {delay}s...")
                time.sleep(delay)

    raise last_error
