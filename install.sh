#!/bin/bash

set -e

echo "Installing Volume Controller..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root" 
   exit 1
fi

# Create config directory
mkdir -p ~/.config/denon

# Check if user is in plugdev group
if ! groups $USER | grep -q '\bplugdev\b'; then
    echo "Adding user $USER to plugdev group (required for USB device access)..."
    sudo usermod -a -G plugdev $USER
    echo "User added to plugdev group. You will need to log out and back in for this to take effect."
fi

# Copy udev rules (requires sudo)
if [ -f "99-volume-controller.rules" ]; then
    echo "Installing udev rules..."
    sudo cp 99-volume-controller.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

# Make Python script executable
chmod +x usb_input.py
echo "Made usb_input.py executable"

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

# Initialize state.json if it doesn't exist or is empty
if [ ! -f ~/.config/denon/state.json ] || [ ! -s ~/.config/denon/state.json ]; then
    echo "Creating initial state.json..."
    echo '{}' > ~/.config/denon/state.json
fi

# Create or update config.json with receiver IP and volume settings
echo "{\"receiver_ip\": \"$receiver_ip\", \"min_volume\": $min_volume, \"max_volume\": $max_volume}" > ~/.config/denon/config.json

echo "Installation complete!"
echo ""
echo "To run the volume controller:"
echo "  ./usb_input.py"
echo ""
echo "Note: You may need to log out and back in for udev rules to take effect."
