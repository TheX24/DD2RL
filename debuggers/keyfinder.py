"""
DrunkDeer G75 Key Discovery Tool
Press each key to discover its index number and identify navigation keys
"""

import hid
import time

VENDOR_ID = 0x352D
PRODUCT_ID = 0x2386
HID_USAGE = 0x0000

class KeyDiscovery:
    def __init__(self):
        self.device = None
        self.key_height_array = [0] * 128
        self.last_key_pressed = {}
        
    def open_device(self):
        print("Searching for DrunkDeer keyboard...")
        devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
        for dev in devices:
            if dev['usage_page'] == 0xFF00 and dev['usage'] == HID_USAGE:
                print(f"Found device: {dev['path'].decode('utf-8')}")
                self.device = hid.device()
                self.device.open_path(dev['path'])
                self.device.set_nonblocking(False)
                return True
        print("Device not found!")
        return False
    
    def send_request_identity(self):
        return self.device.write([0x04, 0xa0, 0x02])
    
    def send_request_keys(self):
        return self.device.write([0x04, 0xb6, 0x03, 0x01])
    
    def process_packet(self, buffer):
        if len(buffer) < 5 or buffer[0] != 0x04:
            return
        
        command = buffer[1]
        if command == 0xa0:
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
            if keynum >= len(self.key_height_array):
                continue
            
            raw_value = buffer[i + 4] if (i + 4) < len(buffer) else 0
            old_value = self.key_height_array[keynum]
            self.key_height_array[keynum] = raw_value
            
            # Detect key press (value went from 0 to something)
            if old_value < 5 and raw_value > 10:
                if keynum not in self.last_key_pressed or (time.time() - self.last_key_pressed[keynum]) > 0.5:
                    print(f"\n🔑 KEY DETECTED: Index {keynum:3d} | Raw Value: {raw_value:2d}")
                    self.last_key_pressed[keynum] = time.time()
    
    def run(self):
        print("=" * 70)
        print("DrunkDeer G75 Key Discovery Tool")
        print("=" * 70)
        print()
        
        if not self.open_device():
            return
        
        print("\nIdentifying keyboard...")
        self.send_request_identity()
        time.sleep(0.1)
        self.device.read(65, timeout_ms=1000)
        
        print("\n✓ Ready!")
        print("\nPress keys to discover their index numbers.")
        print("Focus on navigation cluster: Insert, Delete, Home, End, PgUp, PgDn")
        print("\nPress Ctrl+C to stop\n")
        print("=" * 70)
        
        self.send_request_keys()
        
        try:
            while True:
                data = self.device.read(65, timeout_ms=100)
                if data:
                    self.process_packet(data)
                    if len(data) > 4 and data[4] == 2:
                        time.sleep(0.005)
                        self.send_request_keys()
        except KeyboardInterrupt:
            print("\n\nStopped.")
        finally:
            if self.device:
                self.device.close()

def main():
    discovery = KeyDiscovery()
    discovery.run()

if __name__ == "__main__":
    main()
