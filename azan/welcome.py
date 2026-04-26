import os
import time

from azan.platform_utils import project_root


def play_welcome(catt_path, device_name):
    """Play the welcome voice message on the speaker."""
    from azan import player

    welcome_file = os.path.join(project_root(), "audio", "welcome.mp3")

    if not os.path.isfile(welcome_file):
        print("  Welcome audio not found, skipping.")
        return False

    success = player.play_azan(catt_path, device_name, welcome_file, "100")
    if success:
        time.sleep(5)
    return success
