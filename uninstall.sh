#!/bin/bash

set -e

echo "Uninstalling Volume Controller..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script must NOT be run as root."
   exit 1
fi

# Stop and disable the systemd service if it exists
if systemctl is-active --quiet denon-volume-controller.service; then
    echo "Stopping denon-volume-controller service..."
    sudo systemctl stop denon-volume-controller.service
fi

if systemctl is-enabled --quiet denon-volume-controller.service 2>/dev/null; then
    echo "Disabling denon-volume-controller service..."
    sudo systemctl disable denon-volume-controller.service
fi

# Remove systemd service file
echo "Removing systemd service file..."
sudo rm -f /etc/systemd/system/denon-volume-controller.service
sudo systemctl daemon-reload

# Remove symbolic link from /usr/local/bin
echo "Removing symbolic link from /usr/local/bin..."
sudo rm -f /usr/local/bin/denon-volume-controller

# Remove udev rules
echo "Removing udev rules..."
sudo rm -f /etc/udev/rules.d/99-volume-controller.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Remove installation directory
echo "Removing /opt/denon-volume-controller directory..."
sudo rm -rf /opt/denon-volume-controller

# Remove configuration directory (ask user first)
if [ -d "$HOME/.config/denon" ]; then
    read -p "Remove configuration directory ~/.config/denon? [y/N]: " remove_config
    if [[ $remove_config =~ ^[Yy]$ ]]; then
        echo "Removing configuration directory..."
        rm -rf "$HOME/.config/denon"
    else
        echo "Keeping configuration directory..."
    fi
fi

# Note about plugdev group membership
echo ""
echo "Note: User $USER is still in the plugdev group."
echo "If you want to remove this membership, run:"
echo "  sudo gpasswd -d $USER plugdev"
echo "  (You will need to log out and back in for this to take effect)"

echo ""
echo "Uninstallation complete!"

