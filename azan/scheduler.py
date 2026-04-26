import os
import subprocess

from azan import config
from azan.platform_utils import get_venv_python, project_root


def generate_cron_jobs(cfg, prayer_times):
    """Generate cron job lines for prayer times."""
    python = get_venv_python()
    root = project_root()
    log_file = os.path.join(root, config.get(cfg, "log_file"))
    scan_before = int(config.get(cfg, "scan_before_minutes"))
    volume = config.get(cfg, "volume")

    jobs = []

    for name, time_str in prayer_times.items():
        hour, minute = map(int, time_str.split(":"))

        scan_total = hour * 60 + minute - scan_before
        scan_hour, scan_minute = divmod(scan_total % (24 * 60), 60)

        scan_cmd = f"{python} {root}/check_device.py >> {log_file} 2>&1"
        jobs.append(f"{scan_minute} {scan_hour} * * * {scan_cmd}")

        fajr_flag = " fajr" if name == "Fajr" else ""
        azan_cmd = f"{python} {root}/play_azan.py {volume}{fajr_flag} >> {log_file} 2>&1"
        jobs.append(f"{minute} {hour} * * * {azan_cmd}")

    return jobs


def _persistent_entries(python_path=None, root_dir=None):
    """Generate the persistent @reboot and daily cron entries."""
    if python_path is None:
        python_path = get_venv_python()
    if root_dir is None:
        root_dir = project_root()
    setup_cmd = f"{python_path} {root_dir}/setup_cron.py"
    return [
        f"@reboot sleep 60 && {setup_cmd}",
        f"0 0 * * * {setup_cmd}",
    ]


def write_cron(cron_lines, python_path=None, root_dir=None):
    """Write cron lines to crontab, replacing any previous azan entries."""
    existing = _read_crontab()
    already_set = any("setup_cron.py" in line for line in existing)

    if already_set and not cron_lines:
        return True

    persistent = _persistent_entries(python_path, root_dir)
    all_lines = persistent + cron_lines

    filtered = [
        line for line in existing
        if "play_azan.py" not in line
        and "check_device.py" not in line
        and "setup_cron.py" not in line
    ]

    new_cron = "\n".join(filtered + all_lines) + "\n"

    proc = subprocess.run(
        ["crontab", "-"], input=new_cron, text=True, capture_output=True,
    )
    if proc.returncode != 0:
        print(f"ERROR writing crontab: {proc.stderr}")
        return False
    return True


def _read_crontab():
    """Read current crontab entries as a list of lines."""
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True,
        )
        if result.returncode == 0:
            return [l for l in result.stdout.splitlines() if l.strip()]
    except FileNotFoundError:
        pass
    return []


def print_cron_preview(cron_lines, python_path=None, root_dir=None):
    """Print what cron would look like without writing."""
    persistent = _persistent_entries(python_path, root_dir)

    print("\nCron entries that would be written:")
    print("=" * 60)
    for line in persistent + cron_lines:
        print(line)
    print("=" * 60)
