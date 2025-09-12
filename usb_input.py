#!/usr/bin/env python3
"""
USB Input Reader for device ID 0483:572b
Reads input data from the specified USB device.
"""

import usb.core
import usb.util
import sys
import os
import requests
import json
import re

def load_config():
    """Load configuration from config.json."""
    config_file = os.path.expanduser('~/.config/denon/config.json')
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def check_receiver_connectivity():
    """Check if the receiver IP is reachable."""
    config = load_config()
    receiver_ip = config.get('receiver_ip', '10.10.10.214')
    
    print(f"Checking connectivity to receiver at {receiver_ip}...")
    
    try:
        # Try to reach the status XML endpoint with a short timeout
        test_url = f"http://{receiver_ip}/goform/formMainZone_MainZoneXml.xml"
        response = requests.get(test_url, timeout=3)
        if response.status_code == 200:
            print(f"✓ Successfully connected to receiver at {receiver_ip}")
            return True
        else:
            print(f"✗ Receiver responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot reach receiver at {receiver_ip}: {e}")
        print("Please check:")
        print("  - Receiver is powered on")
        print("  - Network connection is working")
        print("  - IP address is correct in ~/.config/denon/config.json")
        return False

def load_state():
    """Load current state from state.json."""
    state_file = os.path.expanduser('~/.config/denon/state.json')
    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_status_to_state(text_content):
    """Extract MasterVolume and Mute values using regex and save to state.json."""
    try:
        # Find MasterVolume and Mute values using regex
        master_volume = None
        mute_status = None
        
        # Look for <MasterVolume><value>-27.0</value></MasterVolume>
        volume_match = re.search(r'<MasterVolume><value>([^<]+)</value></MasterVolume>', text_content)
        if volume_match:
            master_volume = volume_match.group(1)
        
        # Look for <Mute><value>off</value></Mute>
        mute_match = re.search(r'<Mute><value>([^<]+)</value></Mute>', text_content)
        if mute_match:
            mute_status = mute_match.group(1)
        
        if master_volume is not None or mute_status is not None:
            # Read existing state
            state_file = os.path.expanduser('~/.config/denon/state.json')
            state = {}
            
            if os.path.exists(state_file):
                try:
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                except (json.JSONDecodeError, IOError):
                    state = {}
            
            # Update state
            if master_volume is not None:
                state['MasterVolume'] = master_volume
            if mute_status is not None:
                state['Mute'] = mute_status
            
            # Save state
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"Status saved - Volume: {master_volume}, Mute: {mute_status}")
        
    except Exception as e:
        print(f"Error saving status: {e}")

def volumeUp():
    """Handle volume up command (hex: 01)."""
    print("Action: Volume Up")
    
    # Check volume bounds before making request
    config = load_config()
    state = load_state()
    
    max_volume = config.get('max_volume')
    current_volume = state.get('MasterVolume')
    
    if max_volume is not None and current_volume is not None:
        try:
            if float(current_volume) >= float(max_volume):
                print(f"Volume already at maximum ({current_volume}). Request not sent.")
                return
        except ValueError:
            print("Warning: Could not parse volume values for bounds checking")
    
    try:
        config = load_config()
        receiver_ip = config.get('receiver_ip', '10.10.10.214')
        url = f"http://{receiver_ip}/MainZone/index.put.asp"
        data = "cmd0=PutMasterVolumeBtn%2F%3E"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(url, data=data, headers=headers, timeout=5)
        if response.status_code == 200:
            print("Volume up command sent successfully")
        else:
            print(f"Failed to send volume up command. Status code: {response.status_code}")
        
        # Additional GET request to update status
        try:
            status_url = f"http://{receiver_ip}/goform/formMainZone_MainZoneXml.xml"
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                print("Status update requested successfully")
                save_status_to_state(status_response.text)
            else:
                print(f"Failed to request status update. Status code: {status_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error requesting status update: {e}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending volume up command: {e}")
    
def volumeDown():
    """Handle volume down command (hex: 02)."""
    print("Action: Volume Down")
    
    # Check volume bounds before making request
    config = load_config()
    state = load_state()
    
    min_volume = config.get('min_volume')
    current_volume = state.get('MasterVolume')
    
    if min_volume is not None and current_volume is not None:
        try:
            if float(current_volume) <= float(min_volume):
                print(f"Volume already at minimum ({current_volume}). Request not sent.")
                return
        except ValueError:
            print("Warning: Could not parse volume values for bounds checking")
    
    try:
        config = load_config()
        receiver_ip = config.get('receiver_ip', '10.10.10.214')
        url = f"http://{receiver_ip}/MainZone/index.put.asp"
        data = "cmd0=PutMasterVolumeBtn%2F%3C"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(url, data=data, headers=headers, timeout=5)
        if response.status_code == 200:
            print("Volume down command sent successfully")
        else:
            print(f"Failed to send volume down command. Status code: {response.status_code}")
        
        # Additional GET request to update status
        try:
            status_url = f"http://{receiver_ip}/goform/formMainZone_MainZoneXml.xml"
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                print("Status update requested successfully")
                save_status_to_state(status_response.text)
            else:
                print(f"Failed to request status update. Status code: {status_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error requesting status update: {e}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending volume down command: {e}")
    
def muteToggle():
    """Handle mute toggle command (hex: 04)."""
    print("Action: Mute Toggle")
    
    # Check current mute state
    state = load_state()
    current_mute = state.get('Mute', 'off')
    
    try:
        config = load_config()
        receiver_ip = config.get('receiver_ip', '10.10.10.214')
        url = f"http://{receiver_ip}/MainZone/index.put.asp"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        if current_mute == 'off':
            # Turn mute on
            data = "cmd0=PutVolumeMute%2Fon&cmd1=aspMainZone_WebUpdateStatus%2F"
            print("Turning mute ON")
        else:
            # Turn mute off
            data = "cmd0=PutVolumeMute%2Foff&cmd1=aspMainZone_WebUpdateStatus%2F"
            print("Turning mute OFF")
        
        response = requests.post(url, data=data, headers=headers, timeout=5)
        if response.status_code == 200:
            print("Mute toggle command sent successfully")
        else:
            print(f"Failed to send mute toggle command. Status code: {response.status_code}")
        
        # Additional GET request to update status
        try:
            status_url = f"http://{receiver_ip}/goform/formMainZone_MainZoneXml.xml"
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                print("Status update requested successfully")
                save_status_to_state(status_response.text)
            else:
                print(f"Failed to request status update. Status code: {status_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error requesting status update: {e}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending mute toggle command: {e}")
    
def volumeDownTen():
    """Handle volume down 10 command (hex: 10)."""
    print("Action: Volume Down 10")
    for i in range(10):
        volumeDown()
    
def volumeUpTen():
    """Handle volume up 10 command (hex: 20)."""
    print("Action: Volume Up 10")
    for i in range(10):
        volumeUp()

def detect_hex_command(data):
    """Detect and execute commands based on hex data."""
    if not data:
        return
        
    # Check first byte for command
    command_byte = data[0]
    
    if command_byte == 0x01:
        volumeUp()
    elif command_byte == 0x02:
        volumeDown()
    elif command_byte == 0x04:
        muteToggle()
    elif command_byte == 0x10:
        volumeDownTen()
    elif command_byte == 0x20:
        volumeUpTen()
    else:
        print(f"Unknown command: {command_byte:02x}")
        return False
    
    return True

def find_usb_device(vendor_id, product_id):
    """Find USB device by vendor and product ID."""
    device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
    if device is None:
        raise ValueError(f"USB device {vendor_id:04x}:{product_id:04x} not found")
    return device

def read_usb_input(vendor_id=0x0483, product_id=0x572b):
    """Read input from USB device."""
    
    # Check receiver connectivity before starting
    if not check_receiver_connectivity():
        print("Warning: Receiver not reachable. Volume commands may fail.")
        print("Continuing to monitor USB input...")
        print()
    
    try:
        device = find_usb_device(vendor_id, product_id)
        print(f"Found device: {device}")
        
        try:
            # Detach kernel driver if active
            if device.is_kernel_driver_active(0):
                device.detach_kernel_driver(0)
                print("Detached kernel driver")
        except usb.core.USBError as e:
            print(f"Could not detach kernel driver: {e}")
            if "Operation not permitted" in str(e):
                print("Permission denied. Try running with sudo or check device permissions.")
                return 1
        
        try:
            # Set configuration
            device.set_configuration()
        except usb.core.USBError as e:
            print(f"Could not set configuration: {e}")
            if "Operation not permitted" in str(e) or "Access denied" in str(e):
                print("Permission denied. Try running with sudo.")
                return 1
            raise
        
        # Get endpoint information
        cfg = device.get_active_configuration()
        intf = cfg[(0, 0)]
        
        # Find input endpoint
        ep_in = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        )
        
        if ep_in is None:
            raise ValueError("Input endpoint not found")
        
        print(f"Reading from endpoint: 0x{ep_in.bEndpointAddress:02x}")
        print(f"Max packet size: {ep_in.wMaxPacketSize} bytes")
        print("Press Ctrl+C to stop...")
        print("-" * 50)
        
        # Read data continuously
        while True:
            try:
                data = device.read(ep_in.bEndpointAddress, ep_in.wMaxPacketSize, timeout=1000)
                if data:
                    hex_data = ' '.join(f'{x:02x}' for x in data)
                    print(f"Raw: [{hex_data}] ({len(data)} bytes)")
                    
                    # Detect and handle commands
                    if detect_hex_command(data):
                        print(f"Command detected and executed")
                    
                    # Try to interpret as HID data
                    if len(data) >= 4:  # Typical HID report
                        print(f"HID: modifier={data[0]:02x} reserved={data[1]:02x} keys={' '.join(f'{x:02x}' for x in data[2:])}")
                    
                    # Convert to string if it contains printable characters
                    try:
                        printable = ''.join(chr(x) if 32 <= x <= 126 else '.' for x in data)
                        if any(32 <= x <= 126 for x in data):
                            print(f"ASCII: {printable}")
                    except:
                        pass
                    print()
                    
            except usb.core.USBTimeoutError:
                # No data received, continue waiting
                continue
            except usb.core.USBError as e:
                if "timeout" in str(e).lower():
                    continue
                print(f"USB Error: {e}")
                break
                
    except KeyboardInterrupt:
        print("\nStopping...")
    except PermissionError:
        print("Permission denied. Try running with sudo or check USB permissions.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(read_usb_input())
