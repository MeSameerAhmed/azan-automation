import time

import requests


def pause_tv(config):
    """Pause TV via Home Assistant. No-op if HA not configured."""
    ha_url = config.get("ha_url")
    ha_token = config.get("ha_token")
    entity_id = config.get("tv_entity_id")

    if not all([ha_url, ha_token, entity_id]):
        return False

    state = _get_tv_state(ha_url, ha_token, entity_id)
    if state and state not in ("off", "idle", "standby", "unavailable"):
        print(f"TV state is '{state}', pausing...")
        _ha_call(ha_url, ha_token, "media_player", "media_pause", entity_id)
        return True
    return False


def resume_tv(config):
    """Resume TV via Home Assistant. No-op if HA not configured."""
    ha_url = config.get("ha_url")
    ha_token = config.get("ha_token")
    entity_id = config.get("tv_entity_id")

    if not all([ha_url, ha_token, entity_id]):
        return False

    # Attempt 1: media_play
    _ha_call(ha_url, ha_token, "media_player", "media_play", entity_id)
    time.sleep(3)

    state = _get_tv_state(ha_url, ha_token, entity_id)
    if state == "playing":
        print("TV resumed via media_play")
        return True

    # Attempt 2: turn_on (TV may have gone to standby)
    print("media_play didn't resume, trying turn_on...")
    _ha_call(ha_url, ha_token, "media_player", "turn_on", entity_id)
    time.sleep(5)

    _ha_call(ha_url, ha_token, "media_player", "media_play", entity_id)
    print("TV resume sequence completed")
    return True


def _get_tv_state(ha_url, ha_token, entity_id):
    try:
        resp = requests.get(
            f"{ha_url}/api/states/{entity_id}",
            headers={
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("state")
    except Exception:
        pass
    return None


def _ha_call(ha_url, ha_token, domain, service, entity_id):
    try:
        resp = requests.post(
            f"{ha_url}/api/services/{domain}/{service}",
            headers={
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json",
            },
            json={"entity_id": entity_id},
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"HA {domain}.{service} sent")
        else:
            print(f"HA {domain}.{service} failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"HA {domain}.{service} error: {e}")
