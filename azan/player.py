import subprocess
import time


def play_azan(catt_path, device_name, audio_file, volume):
    """Play azan audio on a Google Home / Chromecast device.

    Args:
        catt_path: Absolute path to catt binary.
        device_name: Chromecast device name.
        audio_file: Path to mp3 file.
        volume: Volume level (0-100 string or int).

    Returns:
        True if playback started successfully, False otherwise.
    """
    if not _run(catt_path, device_name, "volume", str(volume)):
        print("WARNING: Failed to set volume, using current level.")

    time.sleep(1)

    if not _run(catt_path, device_name, "cast", audio_file):
        print("ERROR: Failed to start azan playback.")
        return False

    return True


def _run(catt_path, device_name, *args):
    """Run a catt command. Returns True on success."""
    cmd = [catt_path, "-d", device_name] + list(args)
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"catt error: {e.stderr.strip() or e}")
        return False
    except FileNotFoundError:
        print(f"ERROR: catt not found at {catt_path}")
        return False
