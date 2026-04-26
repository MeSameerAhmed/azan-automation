import os
import platform
import subprocess
import sys


def detect_platform():
    """Detect the current platform.

    Returns dict with:
        type: 'pi_zero' | 'pi' | 'linux' | 'macos'
        arch: machine architecture string
        is_pi: bool
    """
    machine = platform.machine()

    try:
        with open("/proc/device-tree/model") as f:
            model = f.read().strip("\x00").lower()
            if "zero" in model:
                return {"type": "pi_zero", "arch": machine, "is_pi": True}
            return {"type": "pi", "arch": machine, "is_pi": True}
    except FileNotFoundError:
        pass

    if platform.system() == "Darwin":
        return {"type": "macos", "arch": machine, "is_pi": False}

    return {"type": "linux", "arch": machine, "is_pi": False}


def project_root():
    """Absolute path to the azan-automation project root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def venv_dir():
    return os.path.join(project_root(), "venv")


def get_venv_python():
    return os.path.join(venv_dir(), "bin", "python")


def get_venv_catt():
    return os.path.join(venv_dir(), "bin", "catt")


def venv_exists():
    return os.path.isfile(get_venv_python())


def create_venv():
    """Create virtual environment if it doesn't exist."""
    if venv_exists():
        return
    subprocess.run([sys.executable, "-m", "venv", venv_dir()], check=True)


def pip_install_flags(pf):
    """Extra pip flags for constrained devices."""
    if pf["type"] == "pi_zero":
        return ["--no-cache-dir"]
    return []


def ensure_system_deps(pf):
    """Install system-level dependencies if needed.

    Checks if python3 venv module is available; installs via apt on Pi/Linux.
    Returns True if deps are satisfied (either already or after install).
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", "--help"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if pf["is_pi"] or pf["type"] == "linux":
        print("Installing system dependencies (sudo required)...")
        subprocess.run(
            ["sudo", "apt-get", "update", "-qq"], check=False
        )
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "python3-venv", "python3-pip"],
            check=True,
        )
        return True

    if pf["type"] == "macos":
        print("ERROR: python3 venv module not available.")
        print("Install with: xcode-select --install && brew install python3")
        return False

    return False


def reboot():
    """Reboot the system. Only works on Linux/Pi."""
    pf = detect_platform()
    if pf["is_pi"] or pf["type"] == "linux":
        os.system("sudo reboot")
    else:
        print("Reboot requested but not supported on this platform.")
