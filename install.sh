#!/bin/bash

set -e

echo "Installing Volume Controller..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script must NOT be run as root."
   exit 1
fi

# Create installation directory
echo "Creating /opt/denon-volume-controller directory..."
sudo mkdir -p /opt/denon-volume-controller

# Copy all necessary files to installation directory
echo "Copying files to /opt/denon-volume-controller..."
sudo cp usb_input.py /opt/denon-volume-controller/
sudo cp requirements.txt /opt/denon-volume-controller/
sudo cp run.sh /opt/denon-volume-controller/

# Make Python script executable
sudo chmod +x /opt/denon-volume-controller/usb_input.py
sudo chmod +x /opt/denon-volume-controller/run.sh

# Setup venv & install requirements
sudo python3 -m venv /opt/denon-volume-controller
sudo /opt/denon-volume-controller/bin/pip install -r /opt/denon-volume-controller/requirements.txt

# Create config directory
mkdir -p "$HOME/.config/denon"

# Check if original user is in plugdev group
if ! groups $USER | grep -q '\bplugdev\b'; then
    echo "Adding user $USER to plugdev group (required for USB device access)..."
    sudo usermod -a -G plugdev $USER
    echo "User added to plugdev group. You will need to log out and back in for this to take effect."
fi

# Install udev rules
echo "Installing udev rules..."
sudo cp ./99-volume-controller.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

# Check if config already exists and has content
if [ -f "$HOME/.config/denon/config.json" ] && [ $(stat -c%s "$HOME/.config/denon/config.json" 2>/dev/null || echo 0) -gt 10 ]; then
    echo "Configuration file already exists, skipping prompts..."
    # Extract existing values from config
    receiver_ip=$(grep -o '"receiver_ip": *"[^"]*"' "$HOME/.config/denon/config.json" | cut -d'"' -f4)
    min_volume=$(grep -o '"min_volume": *[^,}]*' "$HOME/.config/denon/config.json" | cut -d':' -f2 | tr -d ' ')
    max_volume=$(grep -o '"max_volume": *[^,}]*' "$HOME/.config/denon/config.json" | cut -d':' -f2 | tr -d ' ')
    echo "Using existing configuration: IP=$receiver_ip, Min Volume=$min_volume, Max Volume=$max_volume"
else
    # Prompt for receiver IP address with validation loop
    while true; do
        read -p "Enter your receiver's IP address: " receiver_ip

        # Validate IP address format (basic validation)
        if [[ $receiver_ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            break
        else
            echo "Invalid IP address format. Please enter a valid IP address (e.g., 192.168.1.100)"
        fi
    done

    # Prompt for minimum volume with validation
    while true; do
        read -p "Enter minimum volume (-80.5 to 80.5), 0 is VERY loud: " min_volume

        # Validate volume range (allowing decimal values)
        if [[ $min_volume =~ ^-?[0-9]+(\.[0-9]+)?$ ]] && (( $(echo "$min_volume >= -80.5" | bc -l) )) && (( $(echo "$min_volume <= 80.5" | bc -l) )); then
            break
        else
            echo "Invalid volume. Please enter a number between -80.5 and 80.5."
        fi
    done

    # Prompt for maximum volume with validation
    while true; do
        read -p "Enter maximum volume ($min_volume to 80.5): " max_volume

        # Validate volume range and ensure it's >= min_volume
        if [[ $max_volume =~ ^-?[0-9]+(\.[0-9]+)?$ ]] && (( $(echo "$max_volume >= $min_volume" | bc -l) )) && (( $(echo "$max_volume <= 80.5" | bc -l) )); then
            break
        else
            echo "Invalid volume. Please enter a number between $min_volume and 80.5."
        fi
    done
fi

# Initialize state.json if it doesn't exist or is empty
if [ ! -f "$HOME/.config/denon/state.json" ] || [ ! -s "~/.config/denon/state.json" ]; then
    echo "Creating initial state.json..."
    echo '{}' > "$HOME/.config/denon/state.json"
fi

# Create or update config.json with receiver IP and volume settings
echo "{\"receiver_ip\": \"$receiver_ip\", \"min_volume\": $min_volume, \"max_volume\": $max_volume}" > "$HOME/.config/denon/config.json"

# Create a symbolic link in /usr/local/bin for easy access
sudo ln -sf /opt/denon-volume-controller/run.sh /usr/local/bin/denon-volume-controller

# Add the service to systemd
sudo cp denon-volume-controller.service /etc/systemd/system/denon-volume-controller.service
sudo systemctl daemon-reload
sudo systemctl start denon-volume-controller.service

echo "Installation complete!"
echo ""
echo "Files installed to: /opt/denon-volume-controller/"
echo "Configuration saved to: $HOME/.config/denon/"
echo ""
echo "To run manually:"
echo "  denon-volume-controller"
echo "  or"
echo "  /opt/denon-volume-controller/usb_input.py"
echo ""
echo "To interact with the service:"
echo " Start/Stop/Restart/Status"
echo "  sudo systemctl start denon-volume-controller.service"
echo "  sudo systemctl stop denon-volume-controller.service"
echo "  sudo systemctl restart denon-volume-controller.service"
echo "  sudo systemctl status denon-volume-controller.service"
echo " View Log"
echo "  sudo journalctl -f -u denon-volume-controller"
echo ""
echo "Note: You may need to log out and back in for udev rules to take effect."
echo ""
