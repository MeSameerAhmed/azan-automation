#!/bin/bash
# Azan Automation — Bootstrap Installer
# No prerequisites needed — this script installs Python if missing, then runs install.py

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Detect OS ──────────────────────────────────────────────

detect_os() {
    if [ -f /proc/device-tree/model ]; then
        model=$(tr -d '\0' < /proc/device-tree/model)
        echo "$model" | grep -qi "zero" && echo "pi_zero" && return
        echo "$model" | grep -qi "raspberry" && echo "pi" && return
    fi
    if [ "$(uname -s)" = "Darwin" ]; then
        echo "macos"
    else
        echo "linux"
    fi
}

OS=$(detect_os)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "========================================"
echo "  Azan Automation — Bootstrap Installer"
echo "========================================"
echo "  Detected: $OS ($(uname -m))"
echo ""

# ── Check / Install Python 3 ──────────────────────────────

check_python() {
    if command -v python3 &>/dev/null; then
        version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        # Need 3.7+ (dataclasses, etc.)
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 7 ]; then
            info "Python $version found"
            return 0
        fi
        warn "Python $version found, but 3.7+ required"
    fi
    return 1
}

install_python() {
    info "Installing Python 3..."
    case "$OS" in
        pi_zero|pi|linux)
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y python3 python3-venv python3-pip
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y python3 python3-pip
            elif command -v pacman &>/dev/null; then
                sudo pacman -S --noconfirm python python-pip
            else
                error "Unsupported package manager. Install Python 3.7+ manually."
            fi
            ;;
        macos)
            if command -v brew &>/dev/null; then
                brew install python3
            else
                error "Homebrew not found. Install with: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            fi
            ;;
        *)
            error "Unknown OS. Install Python 3.7+ manually."
            ;;
    esac
}

if check_python; then
    :
else
    install_python
    if ! check_python; then
        error "Python installation failed. Install Python 3.7+ and rerun."
    fi
fi

# ── Run Python Installer ──────────────────────────────────

info "Launching installer..."
echo ""
python3 "$SCRIPT_DIR/install.py"
