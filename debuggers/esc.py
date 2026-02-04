"""
ESC Key Location Test
Run this and press ESC to find its actual index
"""

import hid
import time

VENDOR_ID = 0x352D
PRODUCT_ID = 0x2386

def test_esc():
    print("Searching for DrunkDeer keyboard...")
    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    device = None
    
    for dev in devices:
        if dev['usage_page'] == 0xFF00 and dev['usage'] == 0x0000:
            print(f"Found device: {dev['path'].decode('utf-8')}")
            device = hid.device()
            device.open_path(dev['path'])
            device.set_nonblocking(False)
            break
    
    if not device:
        print("Device not found!")
        return
    
    # Send identity request
    device.write([0x04, 0xa0, 0x02])
    time.sleep(0.1)
    device.read(65, timeout_ms=1000)
    
    print("\n" + "=" * 70)
    print("Press ESC key now...")
    print("Also test F1, F2, F3, etc. to verify function row")
    print("Press Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    key_heights = [0] * 128
    last_pressed = {}
    
    device.write([0x04, 0xb6, 0x03, 0x01])
    
    try:
        while True:
            data = device.read(65, timeout_ms=100)
            if data and len(data) > 4 and data[0] == 0x04 and data[1] == 0xb7:
                packet_type = data[4]
                
                if packet_type == 0:
                    base, length = 0, 59
                elif packet_type == 1:
                    base, length = 59, 59
                elif packet_type == 2:
                    base, length = 118, 8
                else:
                    continue
                
                for i in range(length):
                    idx = base + i
                    if idx >= 128:
                        continue
                    
                    raw_value = data[i + 4] if (i + 4) < len(data) else 0
                    old_value = key_heights[idx]
                    key_heights[idx] = raw_value
                    
                    # Key pressed
                    if old_value < 5 and raw_value > 10:
                        current_time = time.time()
                        if idx not in last_pressed or (current_time - last_pressed[idx]) > 0.5:
                            print(f"KEY DETECTED: Index {idx:3d} | Value: {raw_value:2d}")
                            last_pressed[idx] = current_time
                
                if packet_type == 2:
                    time.sleep(0.005)
                    device.write([0x04, 0xb6, 0x03, 0x01])
    
    except KeyboardInterrupt:
        print("\n\nStopped.")
    finally:
        device.close()

if __name__ == "__main__":
    test_esc()
