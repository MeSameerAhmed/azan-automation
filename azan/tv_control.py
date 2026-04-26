import time

import requests


def _ha_config(config):
    """Extract HA config, return (url, token, entity_id) or None if not configured."""
    ha_url = config.get("ha_url")
    ha_token = config.get("ha_token")
    entity_id = config.get("tv_entity_id")
    if all([ha_url, ha_token, entity_id]):
        return ha_url, ha_token, entity_id
    return None


def _ha_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def pause_tv(config):
    ha = _ha_config(config)
    if not ha:
        return False
    ha_url, ha_token, entity_id = ha

    state = _get_tv_state(ha_url, ha_token, entity_id)
    if state and state not in ("off", "idle", "standby", "unavailable"):
        print(f"TV state is '{state}', pausing...")
        _ha_call(ha_url, ha_token, "media_player", "media_pause", entity_id)
        return True
    return False


def resume_tv(config):
    ha = _ha_config(config)
    if not ha:
        return False
    ha_url, ha_token, entity_id = ha

    _ha_call(ha_url, ha_token, "media_player", "media_play", entity_id)
    time.sleep(3)

    state = _get_tv_state(ha_url, ha_token, entity_id)
    if state == "playing":
        print("TV resumed via media_play")
        return True

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
            headers=_ha_headers(ha_token),
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
            headers=_ha_headers(ha_token),
            json={"entity_id": entity_id},
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"HA {domain}.{service} sent")
        else:
            print(f"HA {domain}.{service} failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"HA {domain}.{service} error: {e}")
