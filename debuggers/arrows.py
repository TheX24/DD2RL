"""
DrunkDeer Arrow Key Diagnostic Tool
Press each arrow key to see what index it triggers
"""

import hid
import time

VENDOR_ID = 0x352D
PRODUCT_ID = 0x2386
HID_USAGE = 0x0000

keyboard_layout = [
    "ESC", "", "", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", 
    "F9", "F10", "F11", "F12", "KP7", "KP8", "KP9", "u1", "u2", "u3", "u4",
    "SWUNG", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", 
    "MINUS", "PLUS", "BACK", "KP4", "KP5", "KP6", "u5", "u6", "u7", "u8",
    "TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", 
    "BRKTS_L", "BRKTS_R", "SLASH_K29", "KP1", "KP2", "KP3", "u9", "u10", "u11", "u12",
    "CAPS", "A", "S", "D", "F", "G", "H", "J", "K", "L", 
    "COLON", "QOTATN", "u13", "RETURN", "u14", "KP0", "KP_DEL", "u15", "u16", "u17", "u18",
    "SHF_L", "EUR_K45", "Z", "X", "C", "V", "B", "N", "M", 
    "COMMA", "PERIOD", "VIRGUE", "u19", "SHF_R", "ARR_UP", "u20", "NUMS", "u21", "u22", "u23", "u24",
    "CTRL_L", "WIN_L", "ALT_L", "u25", "u26", "u27", "SPACE", 
    "u28", "u29", "u30", "ALT_R", "FN1", "APP", "", "ARR_L", 
    "ARR_DW", "ARR_R", "CTRL_R", "u31", "u32", "u33", "u34"
]

key_height_array = [0] * 128
deadzone_min = 2
deadzone_max = 36

def apply_deadzone(value: int) -> int:
    if value < deadzone_min:
        return 0
    elif value > deadzone_max:
        return 40
    else:
        return int((value - deadzone_min) * (40 / (deadzone_max - deadzone_min)))

def open_device():
    print("Searching for DrunkDeer keyboard...")
    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    
    target_device = None
    for dev in devices:
        if dev['usage_page'] == 0xFF00 and dev['usage'] == HID_USAGE:
            target_device = dev
            break
    
    if target_device:
        print(f"Found device: {target_device['path'].decode('utf-8')}")
        device = hid.device()
        device.open_path(target_device['path'])
        device.set_nonblocking(False)
        return device
    
    print("Device not found!")
    return None

def process_packet(device, buffer):
    if len(buffer) < 5 or buffer[0] != 0x04:
        return
    
    command = buffer[1]
    
    if command == 0xa0:
        if buffer[2] == 0x02 and buffer[3] == 0x00:
            print(f"✓ Keyboard identified")
        return
    
    if command != 0xb7:
        return
    
    packet_type = buffer[4]
    
    if packet_type == 0:
        base_position, operation_length = 0, 59
    elif packet_type == 1:
        base_position, operation_length = 59, 59
    elif packet_type == 2:
        base_position, operation_length = 118, 8
    else:
        return
    
    for i in range(operation_length):
        keynum = base_position + i
        if keynum >= len(key_height_array):
            continue
            
        raw_value = buffer[i + 4] if (i + 4) < len(buffer) else 0
        new_value = apply_deadzone(raw_value)
        
        # Detect arrow keys (indices 99, 120, 121, 122)
        if keynum in [99, 120, 121, 122] and new_value > 0 and key_height_array[keynum] == 0:
            key_name = keyboard_layout[keynum] if keynum < len(keyboard_layout) else f"Unknown"
            print(f"\n🔑 KEY DETECTED: Index={keynum}, Name='{key_name}', Value={new_value}/40")
        
        key_height_array[keynum] = new_value

def main():
    print("=" * 70)
    print("DrunkDeer Arrow Key Diagnostic")
    print("=" * 70)
    print("\nThis will show which index each arrow key triggers.")
    print("Press each arrow key (UP, DOWN, LEFT, RIGHT) and watch the output.\n")
    print("Expected indices:")
    print("  Index 99  = ARR_UP")
    print("  Index 120 = ARR_L")
    print("  Index 121 = ARR_DW")
    print("  Index 122 = ARR_R")
    print("\nPress Ctrl+C to exit\n")
    print("=" * 70 + "\n")
    
    device = open_device()
    if not device:
        return
    
    # Send identity request
    device.write([0x04, 0xa0, 0x02])
    time.sleep(0.1)
    data = device.read(65, timeout_ms=1000)
    if data:
        process_packet(device, data)
    
    # Start reading keys
    device.write([0x04, 0xb6, 0x03, 0x01])
    
    try:
        while True:
            data = device.read(65, timeout_ms=100)
            if data:
                process_packet(device, data)
                if len(data) > 4 and data[4] == 2:
                    time.sleep(0.005)
                    device.write([0x04, 0xb6, 0x03, 0x01])
    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        device.close()
        print("Device closed\n")

if __name__ == "__main__":
    main()
