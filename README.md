# Denon AVR-3311CI Volume Controller

This project is for controlling the Denon AVR-3311CI volume over HTTP using a STMicroelectronics USB MultiMedia Controller.

![STMicroelectronics USB MultiMedia Controller](https://raw.githubusercontent.com/pjobson/denon-AVR-3311CI-volume-controller/refs/heads/main/images/STMicroelectronics_USB_MultiMedia_Controller.jpg  "STMicroelectronics USB MultiMedia Controller")

![Denon AVR-3311CI](https://raw.githubusercontent.com/pjobson/denon-AVR-3311CI-volume-controller/refs/heads/main/images/Denon_AVR-3311CI.jpg "Denon AVR-3311CI")

## Notes

The Denon AVR-3311CI uses an old GoAhead-Webs server to which you can configure you unit with. This project basically sends HTTP requests to the server to manipulate the volume and mute.

![Denon Web Interface](https://raw.githubusercontent.com/pjobson/denon-AVR-3311CI-volume-controller/refs/heads/main/images/Denon_Web_Interface.png  "Denon Web Interface")

## Features

- Volume up/down control with configurable limits
- Mute toggle functionality
- Fast volume adjustment (10-step up/down)
- Automatic receiver connectivity checking
- State persistence (current volume and mute status)
- Configurable receiver IP address

## Hardware Requirements

- Denon AVR-3311CI (or compatible receiver)
- STMicroelectronics USB MultiMedia Controller (USB ID: 0483:572b)
- Linux system with Python 3

## Installation

1. **Clone or download** this repository
2. **Run the installer** (will prompt for configuration):

```bash
./install.sh
```

The installer will:

- Add your user to the `plugdev` group for USB access
- Install udev rules for the USB device
- Prompt for your receiver's IP address
- Prompt for minimum and maximum volume levels (-80.5 to 80.5)
- Create configuration files in `~/.config/denon/`
- Adds a systemd service

## Configuration Files

After installation, configuration is stored in:

- **`~/.config/denon/config.json`**: Settings (receiver IP, volume limits)
- **`~/.config/denon/state.json`**: Current state (volume level, mute status)

## Usage

You can use the denon-volume-controller in two ways:

### Option 1: Run directly

```bash
/usr/local/bin/denon-volume-controller
```

To stop use: `CTRL-C`

### Option 2: Use systemd service

#### Start the service
```bash
sudo systemctl start denon-volume-controller
```

#### Enable to start on boot

```bash
sudo systemctl enable denon-volume-controller
```

#### Check service status

```bash
sudo systemctl status denon-volume-controller
```

#### Stop the service

```bash
sudo systemctl stop denon-volume-controller
```

#### Show the log

```bash
sudo journalctl -f -u denon-volume-controller
```

### USB Device Commands

- `0x01`: Volume Up
- `0x02`: Volume Down
- `0x04`: Mute Toggle
- `0x10`: Volume Down 10 steps
- `0x20`: Volume Up 10 steps
- `0x00`: Do Nothing

## Volume Limits

The controller respects the minimum and maximum volume limits set during installation. Commands that would exceed these limits are ignored with a warning message.

## Troubleshooting

### Permission Issues

- Ensure you're in the `plugdev` group: `groups $USER`
- Log out and back in after installation
- Check udev rules are installed: `ls /etc/udev/rules.d/*volume*`

### Network Issues

- Verify receiver IP address in `~/.config/denon/config.json`
- Ensure receiver is powered on and connected to network
- Test connectivity: `ping <receiver_ip>`

### USB Device Issues  

- Check device is connected: `lsusb | grep 0483:572b`
- Verify udev rules are active: `sudo udevadm trigger`

## Technical Details

This project could potentially be adapted to work with other Denon receivers and USB input devices by modifying the USB vendor/product IDs and HTTP endpoints.
