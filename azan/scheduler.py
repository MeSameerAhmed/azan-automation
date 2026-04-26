import os
import subprocess

from azan.platform_utils import get_venv_python, project_root


def generate_cron_jobs(config, prayer_times):
    """Generate cron job lines for prayer times.

    Args:
        config: Config dict.
        prayer_times: Dict of prayer_name -> "HH:MM".

    Returns:
        list of cron line strings.
    """
    python = get_venv_python()
    root = project_root()
    log_file = os.path.join(root, config.get("log_file", "azan.log"))
    scan_before = int(config.get("scan_before_minutes", 5))
    volume = config.get("volume", "100")

    jobs = []

    for name, time_str in prayer_times.items():
        hour, minute = map(int, time_str.split(":"))

        # Scan job (N minutes before prayer)
        scan_total = hour * 60 + minute - scan_before
        scan_hour, scan_minute = divmod(scan_total % (24 * 60), 60)

        scan_cmd = f"{python} {root}/check_device.py >> {log_file} 2>&1"
        jobs.append(f"{scan_minute} {scan_hour} * * * {scan_cmd}")

        # Azan job (at exact prayer time)
        fajr_flag = " fajr" if name == "Fajr" else ""
        azan_cmd = f"{python} {root}/play_azan.py {volume}{fajr_flag} >> {log_file} 2>&1"
        jobs.append(f"{minute} {hour} * * * {azan_cmd}")

    return jobs


def write_cron(cron_lines, python_path=None, root_dir=None):
    """Write cron lines to crontab, replacing any previous azan entries.

    Also adds @reboot and daily midnight entries for setup_cron.py.
    """
    if python_path is None:
        python_path = get_venv_python()
    if root_dir is None:
        root_dir = project_root()

    # Add persistent entries (setup_cron on reboot + daily)
    setup_cmd = f"{python_path} {root_dir}/setup_cron.py"
    persistent = [
        f"@reboot sleep 60 && {setup_cmd}",
        f"0 0 * * * {setup_cmd}",
    ]

    all_lines = persistent + cron_lines

    # Read existing crontab, strip old azan entries
    existing = _read_crontab()
    filtered = [
        line for line in existing
        if "play_azan.py" not in line
        and "check_device.py" not in line
        and "setup_cron.py" not in line
    ]

    new_cron = "\n".join(filtered + all_lines) + "\n"

    # Write via crontab command
    proc = subprocess.run(
        ["crontab", "-"],
        input=new_cron,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(f"ERROR writing crontab: {proc.stderr}")
        return False
    return True


def _read_crontab():
    """Read current crontab entries as a list of lines."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return [l for l in result.stdout.splitlines() if l.strip()]
    except FileNotFoundError:
        pass
    return []


def print_cron_preview(cron_lines, python_path=None, root_dir=None):
    """Print what cron would look like without writing."""
    if python_path is None:
        python_path = get_venv_python()
    if root_dir is None:
        root_dir = project_root()

    setup_cmd = f"{python_path} {root_dir}/setup_cron.py"

    print("\nCron entries that would be written:")
    print("=" * 60)
    print(f"@reboot sleep 60 && {setup_cmd}")
    print(f"0 0 * * * {setup_cmd}")
    for line in cron_lines:
        print(line)
    print("=" * 60)
