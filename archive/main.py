"""
DrunkDeer G75 Magnetic Key to Controller Emulation
Reads analog key press data from DrunkDeer G75 keyboard and maps to virtual Xbox controller
For racing games like Forza Motorfest - supports throttle, brake, and steering
"""

import hid
import time
import vgamepad as vg
from dataclasses import dataclass
from typing import Callable, Dict, Optional
import sys

# Configuration - UPDATED FOR YOUR KEYBOARD
VENDOR_ID = 0x352D
PRODUCT_ID = 0x2386  # Your keyboard's actual Product ID
HID_USAGE = 0x0000   # Usage for raw data interface

@dataclass
class KeyAction:
    """Maps a key to a controller action"""
    function: Callable
    inverse: bool = False

class G75Controller:
    def __init__(self, deadzone_min=2, deadzone_max=36, polling_interval_ms=5):
        self.device = None
        self.gamepad = vg.VX360Gamepad()
        self.key_height_array = [0] * 128
        self.key_action_map: Dict[int, KeyAction] = {}
        self.deadzone_min = deadzone_min
        self.deadzone_max = deadzone_max
        self.polling_interval_ms = polling_interval_ms
        self.keyboard_id = 0
        
        # Store current analog values for combining inputs
        self.left_stick_x = 0.0
        self.left_stick_y = 0.0
        self.right_stick_x = 0.0
        self.right_stick_y = 0.0
        self.left_trigger_val = 0.0
        self.right_trigger_val = 0.0
        
        # Keyboard layout (126 keys)
        self.keyboard_layout = [
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
    
    def open_device(self) -> bool:
        """Open HID device connection"""
        print("Searching for DrunkDeer keyboard...")
        devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
        
        target_device = None
        for dev in devices:
            # Look for the interface with usage_page 0xFF00 and usage 0x0000
            if dev['usage_page'] == 0xFF00 and dev['usage'] == HID_USAGE:
                target_device = dev
                break
        
        if target_device:
            print(f"Found device: {target_device['path'].decode('utf-8')}")
            self.device = hid.device()
            self.device.open_path(target_device['path'])
            self.device.set_nonblocking(False)
            return True
        
        print("Device not found! Make sure your DrunkDeer keyboard is connected.")
        return False
    
    def send_request_keys(self) -> int:
        """Send request to keyboard for key height data"""
        return self.device.write([0x04, 0xb6, 0x03, 0x01])
    
    def send_request_identity(self) -> int:
        """Request keyboard identity"""
        return self.device.write([0x04, 0xa0, 0x02])
    
    def identify_keyboard(self, byte5: int, byte6: int, byte7: int):
        """Identify keyboard model from response"""
        if byte5 == 11 and byte6 == 4 and byte7 == 5:
            self.keyboard_id = 754  # G75
            print("✓ Connected to DrunkDeer G75")
        elif byte5 == 11 and byte6 == 1 and byte7 == 1:
            self.keyboard_id = 75  # A75
            print("✓ Connected to DrunkDeer A75")
        elif byte5 == 11 and byte6 == 4 and byte7 == 3:
            self.keyboard_id = 750  # A75 Pro
            print("✓ Connected to DrunkDeer A75 Pro")
        else:
            print(f"✓ Connected to DrunkDeer keyboard (ID: {byte5}, {byte6}, {byte7})")
            self.keyboard_id = 1  # Mark as identified but unknown model
    
    def apply_deadzone(self, value: int) -> int:
        """Apply deadzone to raw key height value"""
        if value < self.deadzone_min:
            return 0
        elif value > self.deadzone_max:
            return 40
        else:
            return int((value - self.deadzone_min) * (40 / (self.deadzone_max - self.deadzone_min)))
    
    def scale_to_byte(self, percent: float) -> int:
        """Scale 0.0-1.0 to BYTE range (0-255)"""
        return max(0, min(255, int(percent * 255)))
    
    def register_key_action(self, key_name: str, action_func: Callable, inverse: bool = False):
        """Register a key to controller action mapping"""
        try:
            keycode = self.keyboard_layout.index(key_name)
            self.key_action_map[keycode] = KeyAction(action_func, inverse)
            print(f"  Mapped: {key_name} (keycode {keycode})")
        except ValueError:
            print(f"  ⚠ Key '{key_name}' not found in layout")
    
    def action_left_stick_x_positive(self, percent: float, inverse: bool):
        self.left_stick_x += percent
    
    def action_left_stick_x_negative(self, percent: float, inverse: bool):
        self.left_stick_x -= percent
    
    def action_left_stick_y_positive(self, percent: float, inverse: bool):
        self.left_stick_y += percent * 0.5
    
    def action_left_stick_y_negative(self, percent: float, inverse: bool):
        self.left_stick_y -= percent * 0.5
    
    def action_right_stick_x_positive(self, percent: float, inverse: bool):
        self.right_stick_x += percent * 0.5
    
    def action_right_stick_x_negative(self, percent: float, inverse: bool):
        self.right_stick_x -= percent * 0.5
    
    def action_right_stick_y_positive(self, percent: float, inverse: bool):
        self.right_stick_y += percent * 0.5
    
    def action_right_stick_y_negative(self, percent: float, inverse: bool):
        self.right_stick_y -= percent * 0.5
    
    def action_left_trigger(self, percent: float, inverse: bool):
        self.left_trigger_val = max(self.left_trigger_val, percent)
    
    def action_right_trigger(self, percent: float, inverse: bool):
        self.right_trigger_val = max(self.right_trigger_val, percent)
    
    def process_key_height(self, keycode: int, travel_percent: float):
        if keycode in self.key_action_map:
            action = self.key_action_map[keycode]
            action.function(travel_percent, action.inverse)
    
    def process_packet(self, buffer: list):
        if len(buffer) < 5 or buffer[0] != 0x04:
            return
        
        command = buffer[1]
        
        if command == 0xa0:
            if buffer[2] == 0x02 and buffer[3] == 0x00:
                self.identify_keyboard(buffer[5], buffer[6], buffer[7])
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
            new_value = self.apply_deadzone(raw_value)
            percent = new_value / 40.0
            self.key_height_array[keynum] = new_value
            self.process_key_height(keynum, percent)
        
        if packet_type == 2:
            self.gamepad.left_joystick_float(
                x_value_float=max(-1.0, min(1.0, self.left_stick_x)),
                y_value_float=max(-1.0, min(1.0, self.left_stick_y))
            )
            self.gamepad.right_joystick_float(
                x_value_float=max(-1.0, min(1.0, self.right_stick_x)),
                y_value_float=max(-1.0, min(1.0, self.right_stick_y))
            )
            self.gamepad.left_trigger(self.scale_to_byte(self.left_trigger_val))
            self.gamepad.right_trigger(self.scale_to_byte(self.right_trigger_val))
            
            self.gamepad.update()
            
            self.left_stick_x = 0.0
            self.left_stick_y = 0.0
            self.right_stick_x = 0.0
            self.right_stick_y = 0.0
            self.left_trigger_val = 0.0
            self.right_trigger_val = 0.0
    
    def setup_racing_config(self):
        print("\nSetting up Racing Game configuration:")
        self.register_key_action("W", self.action_right_trigger)
        self.register_key_action("S", self.action_left_trigger)
        self.register_key_action("A", self.action_left_stick_x_negative)
        self.register_key_action("D", self.action_left_stick_x_positive)
        print()
    
    def setup_custom_config(self):
        print("\nSetting up Custom configuration:")
        self.register_key_action("ARR_UP", self.action_right_stick_y_positive)
        self.register_key_action("ARR_DW", self.action_right_stick_y_negative)
        self.register_key_action("ARR_L", self.action_right_stick_x_negative)
        self.register_key_action("ARR_R", self.action_right_stick_x_positive)
        print()
    
    def run(self, config_mode: str = "racing"):
        print("=" * 60)
        print("DrunkDeer -> Xbox Controller Emulator")
        print("=" * 60)
        
        if not self.open_device():
            print("\n❌ Failed to open device. Exiting.")
            return
        
        print("\nIdentifying keyboard...")
        self.send_request_identity()
        time.sleep(0.1)
        
        try:
            data = self.device.read(65, timeout_ms=1000)
            if data:
                self.process_packet(data)
        except Exception as e:
            print(f"❌ Error reading identity: {e}")
            return
        
        if self.keyboard_id == 0:
            print("❌ Failed to identify keyboard. Exiting.")
            return
        
        if config_mode == "racing":
            self.setup_racing_config()
        elif config_mode == "custom":
            self.setup_custom_config()
            self.setup_racing_config()
        
        print("✓ Virtual Xbox 360 controller created")
        print("\n" + "=" * 60)
        print("CONTROLS:")
        print("  W = Throttle (Right Trigger)")
        print("  S = Brake (Left Trigger)")
        print("  A = Steer Left")
        print("  D = Steer Right")
        if config_mode == "custom":
            print("  Arrow Keys = Right Stick (Camera)")
        print("\nPress Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        self.send_request_keys()
        packet_count = 0
        
        try:
            while True:
                data = self.device.read(65, timeout_ms=100)
                
                if data:
                    self.process_packet(data)
                    packet_count += 1
                    
                    if len(data) > 4 and data[4] == 2:
                        time.sleep(self.polling_interval_ms / 1000.0)
                        self.send_request_keys()
                        
                        if packet_count % 200 == 0:
                            print(f"Running... (packets: {packet_count})", end="\r")
        
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("Stopping gracefully...")
            print("=" * 60)
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
        finally:
            if self.device:
                self.device.close()
                print("✓ Device closed")
            print("✓ Exited cleanly\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DrunkDeer to Xbox Controller Emulator"
    )
    parser.add_argument("--config", choices=["racing", "custom"], default="racing")
    parser.add_argument("--deadzone-min", type=int, default=2)
    parser.add_argument("--deadzone-max", type=int, default=36)
    parser.add_argument("--poll-interval", type=int, default=5)
    
    args = parser.parse_args()
    
    controller = G75Controller(
        deadzone_min=args.deadzone_min,
        deadzone_max=args.deadzone_max,
        polling_interval_ms=args.poll_interval
    )
    
    controller.run(config_mode=args.config)

if __name__ == "__main__":
    main()
