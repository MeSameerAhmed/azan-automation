#!/usr/bin/env bash
# Pi Zero 2 W one-shot setup script
# Run this on a FRESH Pi after flashing with Raspberry Pi Imager
#
# Usage:
#   1. Flash Pi with Raspberry Pi Imager (enable SSH, set user: raspi / shafiq@123)
#   2. SSH in: ssh raspi<IP>
#   3. Copy this repo: scp -r /path/to/azan-automation raspi@<IP>:~/azan-automation
#   4. Run: cd ~/azan-automation && chmod +x setup-pi.sh && ./setup-pi.sh
#
# What this does:
#   - Disables WiFi power save
#   - Masks sleep/suspend/hibernate
#   - Disables HDMI blanking
#   - Moves logs + /tmp + /var/log to RAM (protects SD card)
#   - Enables rpi-connect with auto-restart
#   - Installs ZeroTier and joins network
#   - Adds SSH public key for passwordless login
#   - Runs the azan-automation installer
#
# After this: authorize the new ZeroTier device at my.zerotier.com

set -euo pipefail

# ---- CONFIG ----
ZEROTIER_NETWORK="XXXX_XXXX_XXXX_XXXX"  # Replace with your ZeroTier network ID
SSH_PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQD1K0xJnrB4M9z9j41eCJsFNMCU0TUwz9ISgv/BnXItmUVd/va2XbwjYiOc7y/fXNpk0aBsEbaHgLT34QYK+CUqnGRAJaP0QBJrpJgehmdpjHANuyLrAXE/SQLW3a2oEoRmdlBqgGPiAjqVuEdKdVZTPKNgNy6ZRA1b7K8+52H1BQ== sameer-new-temp-laptop"
NETPLAN_FILE="/etc/netplan/90-NM-135773cc-6a85-3716-8553-7b236f25f41e.yaml"
# ---- END CONFIG ----

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }
step() { echo ""; echo -e "${GREEN}=== $1 ===${NC}"; }

# Check running on Pi
if [ ! -f /proc/device-tree/model ]; then
    fail "This script must run on a Raspberry Pi"
fi
ok "Running on $(cat /proc/device-tree/model | tr '\0' ' ')"

# ---- 1. WiFi power save ----
step "1/8 Disable WiFi power save"
if grep -q "wifi.powersave" "$NETPLAN_FILE" 2>/dev/null; then
    ok "Already configured"
else
    sudo sed -i '/proxy._: ""$/a\              wifi.powersave: "2"' "$NETPLAN_FILE"
    sudo netplan apply 2>&1 || true
    ok "WiFi power save disabled in netplan"
fi

# ---- 2. Mask sleep targets ----
step "2/8 Disable sleep/suspend/hibernate"
for target in sleep.target suspend.target hibernate.target hybrid-sleep.target; do
    sudo systemctl mask "$target" 2>/dev/null
done
ok "All sleep targets masked"

# ---- 2b. Passwordless reboot ----
if [ -f /etc/sudoers.d/raspi-reboot ]; then
    ok "Passwordless reboot already configured"
else
    echo "raspi ALL=(ALL) NOPASSWD: /usr/sbin/reboot" | sudo tee /etc/sudoers.d/raspi-reboot > /dev/null
    sudo chmod 440 /etc/sudoers.d/raspi-reboot
    ok "Passwordless reboot for raspi user"
fi

# ---- 3. HDMI blanking ----
step "3/8 Disable HDMI blanking"
CONFIG_FILE="/boot/firmware/config.txt"
[ -f "$CONFIG_FILE" ] || CONFIG_FILE="/boot/config.txt"
if grep -q "^hdmi_blanking" "$CONFIG_FILE" 2>/dev/null; then
    ok "Already configured"
else
    echo "hdmi_blanking=0" | sudo tee -a "$CONFIG_FILE" > /dev/null
    ok "HDMI blanking disabled"
fi

# ---- 4. Logs + tmp in RAM ----
step "4/8 Move logs and /tmp to RAM (protect SD card)"

# Journald to RAM with 1-day retention
sudo tee /etc/systemd/journald.conf > /dev/null <<'EOF'
[Journal]
Storage=volatile
Compress=yes
SystemMaxUse=50M
SystemKeepFree=10M
MaxRetentionSec=1day
EOF
sudo systemctl restart systemd-journald 2>/dev/null || true
ok "Journald: RAM, 1-day retention, 50MB max"

# /tmp and /var/log to tmpfs
if grep -q "tmpfs /tmp" /etc/fstab 2>/dev/null; then
    ok "/tmp already in tmpfs"
else
    echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=50m 0 0" | sudo tee -a /etc/fstab > /dev/null
    echo "tmpfs /var/log tmpfs defaults,noatime,nosuid,size=30m 0 0" | sudo tee -a /etc/fstab > /dev/null
    ok "/tmp and /var/log added to tmpfs"
fi

# ---- 4b. Azan log rotation ----
if [ -f /etc/logrotate.d/azan ]; then
    ok "Logrotate already configured"
else
    sudo tee /etc/logrotate.d/azan > /dev/null <<'EOF'
/home/raspi/azan-automation/azan.log {
    weekly
    rotate 1
    missingok
    notifempty
    compress
}
EOF
    ok "Azan log rotation: weekly, keep only current"
fi

# ---- 5. rpi-connect ----
step "5/8 Enable rpi-connect with auto-restart"
sudo loginctl enable-linger raspi 2>/dev/null || true
mkdir -p ~/.config/systemd/user/rpi-connect.service.d
cat > ~/.config/systemd/user/rpi-connect.service.d/restart.conf <<'EOF'
[Service]
Restart=on-failure
RestartSec=10
EOF
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable rpi-connect.service 2>/dev/null || true
systemctl --user start rpi-connect.service 2>/dev/null || true
ok "rpi-connect enabled with auto-restart"

# ---- 6. ZeroTier ----
step "6/8 Install ZeroTier"
if command -v zerotier-cli &>/dev/null; then
    ok "ZeroTier already installed"
else
    curl -s https://install.zerotier.com | sudo bash
    ok "ZeroTier installed"
fi

# Join network (retry a few times)
step "6/8 Join ZeroTier network"
for i in $(seq 1 5); do
    if sudo zerotier-cli join "$ZEROTIER_NETWORK" 2>/dev/null; then
        ok "Joined ZeroTier network $ZEROTIER_NETWORK"
        break
    fi
    echo "  Retrying in 5s... (attempt $i/5)"
    sleep 5
done

# ---- 7. SSH key ----
step "7/8 Add SSH public key"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
if grep -q "sameer-new-temp-laptop" ~/.ssh/authorized_keys 2>/dev/null; then
    ok "SSH key already present"
else
    echo "$SSH_PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    ok "SSH key added"
fi

# ---- 8. Azan installer ----
step "8/8 Run azan-automation installer"
echo "This is interactive — you'll need to answer prompts."
echo "Press Enter to start the installer, or Ctrl+C to skip."
read -r
cd ~/azan-automation
chmod +x setup.sh
./setup.sh

echo ""
echo "========================================="
echo "  SETUP COMPLETE"
echo "========================================="
echo ""
echo "IMPORTANT: Authorize the new ZeroTier device at:"
echo "  https://my.zerotier.com/network/$ZEROTIER_NETWORK"
echo ""
echo "ZeroTier device ID: $(sudo zerotier-cli info 2>/dev/null | awk '{print $3}')"
echo ""
echo "Verify with:"
echo "  ssh raspi@<ZEROTIER_IP>"
echo ""
