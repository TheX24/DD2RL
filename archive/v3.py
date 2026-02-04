"""
DrunkDeer G75 Magnetic Key to Controller Emulation
Reads analog key press data from DrunkDeer keyboard and maps to virtual Xbox controller
Now with JSON config file support and keyboard input suppression
"""

import hid
import time
import vgamepad as vg
from dataclasses import dataclass
from typing import Callable, Dict, Set
import json
import sys
import os
import threading
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

# Configuration
VENDOR_ID = 0x352D
PRODUCT_ID = 0x2386
HID_USAGE = 0x0000

@dataclass
class KeyAction:
    """Maps a key to a controller action"""
    function: Callable
    inverse: bool = False
    description: str = ""

class KeyboardSuppressor:
    """Suppresses keyboard inputs from reaching the game"""
    
    def __init__(self, suppress_keys: Set[str], toggle_key: str = "f12"):
        self.suppress_keys = suppress_keys
        self.toggle_key = toggle_key.lower()
        self.suppression_active = True
        self.listener = None
        
    def parse_special_key(self, key_name: str):
        """Convert key name string to pynput Key"""
        key_map = {
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
            'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
            'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
            'space': Key.space, 'shift': Key.shift, 'shift_l': Key.shift_l,
            'shift_r': Key.shift_r, 'ctrl': Key.ctrl, 'alt': Key.alt,
            'left': Key.left, 'right': Key.right, 'up': Key.up, 'down': Key.down,
            'esc': Key.esc, 'escape': Key.esc, 'tab': Key.tab, 'enter': Key.enter
        }
        return key_map.get(key_name.lower())
    
    def normalize_key(self, key):
        """Convert pynput key to normalized string"""
        try:
            # Character key
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
        except:
            pass
        
        # Special key
        if isinstance(key, Key):
            return key.name.lower()
        
        return None
    
    def on_press(self, key):
        """Handle key press events"""
        normalized = self.normalize_key(key)
        
        # Check for toggle key
        if normalized == self.toggle_key:
            self.suppression_active = not self.suppression_active
            status = "ON" if self.suppression_active else "OFF"
            print(f"\n🔒 Keyboard suppression: {status}")
            return True  # Don't suppress the toggle key itself
        
        # Suppress if active and key is in suppress list
        if self.suppression_active and normalized in self.suppress_keys:
            return False  # Suppress this key
        
        return True  # Allow key through
    
    def start(self):
        """Start the keyboard listener"""
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            suppress=True
        )
        self.listener.start()
        status = "ON" if self.suppression_active else "OFF"
        print(f"\n🔒 Keyboard suppression: {status}")
        print(f"   Toggle key: {self.toggle_key.upper()}")
    
    def stop(self):
        """Stop the keyboard listener"""
        if self.listener:
            self.listener.stop()

class G75Controller:
    def __init__(self, config_file="crew_motorfest_config.json", deadzone_min=2, deadzone_max=36, polling_interval_ms=5):
        self.device = None
        self.gamepad = vg.VX360Gamepad()
        self.key_height_array = [0] * 128
        self.key_action_map: Dict[int, KeyAction] = {}
        self.deadzone_min = deadzone_min
        self.deadzone_max = deadzone_max
        self.polling_interval_ms = polling_interval_ms
        self.keyboard_id = 0
        self.config_file = config_file
        self.suppressor = None
        
        # Store current analog values
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
        
        # DrunkDeer to standard key mapping for suppression
        self.drunkdeer_to_standard = {
            "W": "w", "A": "a", "S": "s", "D": "d",
            "E": "e", "R": "r", "F": "f", "T": "t",
            "Q": "q", "Z": "z", "X": "x", "C": "c",
            "V": "v", "B": "b", "H": "h", "N": "n",
            "SPACE": "space", "SHF_L": "shift_l", "SHF_R": "shift_r",
            "ARR_L": "left", "ARR_R": "right", "ARR_UP": "up", "ARR_DW": "down",
            "ESC": "esc", "TAB": "tab", "RETURN": "enter"
        }
    
    def load_config(self):
        """Load key mappings from JSON config file"""
        if not os.path.exists(self.config_file):
            print(f"⚠ Config file '{self.config_file}' not found. Using default racing config.")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            game_name = config.get('game', 'Unknown')
            print(f"\n📋 Loading config for: {game_name}")
            print(f"   Description: {config.get('description', 'N/A')}")
            
            # Get suppression settings
            suppression_config = config.get('suppression', {})
            toggle_key = suppression_config.get('toggle_key', 'f12')
            enable_suppression = suppression_config.get('enabled', True)
            
            # Collect keys to suppress
            suppress_keys = set()
            
            # Load analog mappings
            analog_maps = config.get('controller_mappings', {}).get('analog', {})
            for action, mapping in analog_maps.items():
                key_name = mapping['drunkdeer_key']
                controller_action = mapping['controller']
                description = mapping.get('description', action)
                
                # Add to suppression list
                standard_key = self.drunkdeer_to_standard.get(key_name, key_name.lower())
                suppress_keys.add(standard_key)
                
                if 'LEFT_STICK_X_POSITIVE' in controller_action:
                    self.register_key_action(key_name, self.action_left_stick_x_positive, description=description)
                elif 'LEFT_STICK_X_NEGATIVE' in controller_action:
                    self.register_key_action(key_name, self.action_left_stick_x_negative, description=description)
                elif 'LEFT_STICK_Y_POSITIVE' in controller_action:
                    self.register_key_action(key_name, self.action_left_stick_y_positive, description=description)
                elif 'LEFT_STICK_Y_NEGATIVE' in controller_action:
                    self.register_key_action(key_name, self.action_left_stick_y_negative, description=description)
                elif 'RIGHT_STICK_X_POSITIVE' in controller_action:
                    self.register_key_action(key_name, self.action_right_stick_x_positive, description=description)
                elif 'RIGHT_STICK_X_NEGATIVE' in controller_action:
                    self.register_key_action(key_name, self.action_right_stick_x_negative, description=description)
                elif 'RIGHT_STICK_Y_POSITIVE' in controller_action:
                    self.register_key_action(key_name, self.action_right_stick_y_positive, description=description)
                elif 'RIGHT_STICK_Y_NEGATIVE' in controller_action:
                    self.register_key_action(key_name, self.action_right_stick_y_negative, description=description)
                elif 'RIGHT_TRIGGER' in controller_action:
                    self.register_key_action(key_name, self.action_right_trigger, description=description)
                elif 'LEFT_TRIGGER' in controller_action:
                    self.register_key_action(key_name, self.action_left_trigger, description=description)
            
            # Load button mappings
            button_maps = config.get('controller_mappings', {}).get('buttons', {})
            for action, mapping in button_maps.items():
                key_name = mapping['drunkdeer_key']
                controller_button = mapping['controller']
                description = mapping.get('description', action)
                
                # Add to suppression list
                standard_key = self.drunkdeer_to_standard.get(key_name, key_name.lower())
                suppress_keys.add(standard_key)
                
                # Map buttons
                if 'A_BUTTON' in controller_button:
                    self.register_key_action(key_name, self.action_button_a, description=description)
                elif 'B_BUTTON' in controller_button:
                    self.register_key_action(key_name, self.action_button_b, description=description)
                elif 'X_BUTTON' in controller_button:
                    self.register_key_action(key_name, self.action_button_x, description=description)
                elif 'Y_BUTTON' in controller_button:
                    self.register_key_action(key_name, self.action_button_y, description=description)
                elif 'LEFT_BUMPER' in controller_button:
                    self.register_key_action(key_name, self.action_left_bumper, description=description)
                elif 'RIGHT_BUMPER' in controller_button:
                    self.register_key_action(key_name, self.action_right_bumper, description=description)
                elif 'START' in controller_button:
                    self.register_key_action(key_name, self.action_start, description=description)
                elif 'DPAD_UP' in controller_button:
                    self.register_key_action(key_name, self.action_dpad_up, description=description)
                elif 'DPAD_DOWN' in controller_button:
                    self.register_key_action(key_name, self.action_dpad_down, description=description)
            
            # Setup keyboard suppression
            if enable_suppression and suppress_keys:
                self.suppressor = KeyboardSuppressor(suppress_keys, toggle_key)
                self.suppressor.start()
            else:
                print("\n⚠ Keyboard suppression disabled in config")
            
            return True
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def open_device(self) -> bool:
        """Open HID device connection"""
        print("Searching for DrunkDeer keyboard...")
        devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
        
        target_device = None
        for dev in devices:
            if dev['usage_page'] == 0xFF00 and dev['usage'] == HID_USAGE:
                target_device = dev
                break
        
        if target_device:
            print(f"Found device: {target_device['path'].decode('utf-8')}")
            self.device = hid.device()
            self.device.open_path(target_device['path'])
            self.device.set_nonblocking(False)
            return True
        
        print("Device not found!")
        return False
    
    def send_request_keys(self) -> int:
        return self.device.write([0x04, 0xb6, 0x03, 0x01])
    
    def send_request_identity(self) -> int:
        return self.device.write([0x04, 0xa0, 0x02])
    
    def identify_keyboard(self, byte5: int, byte6: int, byte7: int):
        if byte5 == 11 and byte6 == 4 and byte7 == 5:
            self.keyboard_id = 754
            print("✓ Connected to DrunkDeer G75")
        elif byte5 == 11 and byte6 == 1 and byte7 == 1:
            self.keyboard_id = 75
            print("✓ Connected to DrunkDeer A75")
        elif byte5 == 11 and byte6 == 4 and byte7 == 3:
            self.keyboard_id = 750
            print("✓ Connected to DrunkDeer A75 Pro")
        else:
            print(f"✓ Connected to DrunkDeer keyboard (ID: {byte5}, {byte6}, {byte7})")
            self.keyboard_id = 1
    
    def apply_deadzone(self, value: int) -> int:
        if value < self.deadzone_min:
            return 0
        elif value > self.deadzone_max:
            return 40
        else:
            return int((value - self.deadzone_min) * (40 / (self.deadzone_max - self.deadzone_min)))
    
    def scale_to_byte(self, percent: float) -> int:
        return max(0, min(255, int(percent * 255)))
    
    def register_key_action(self, key_name: str, action_func: Callable, inverse: bool = False, description: str = ""):
        try:
            keycode = self.keyboard_layout.index(key_name)
            self.key_action_map[keycode] = KeyAction(action_func, inverse, description)
            print(f"  ✓ {key_name:8s} -> {description}")
        except ValueError:
            print(f"  ⚠ Key '{key_name}' not found in layout")
    
    # Analog stick actions
    def action_left_stick_x_positive(self, percent: float, inverse: bool):
        self.left_stick_x += percent
    
    def action_left_stick_x_negative(self, percent: float, inverse: bool):
        self.left_stick_x -= percent
    
    def action_left_stick_y_positive(self, percent: float, inverse: bool):
        self.left_stick_y += percent
    
    def action_left_stick_y_negative(self, percent: float, inverse: bool):
        self.left_stick_y -= percent
    
    def action_right_stick_x_positive(self, percent: float, inverse: bool):
        self.right_stick_x += percent
    
    def action_right_stick_x_negative(self, percent: float, inverse: bool):
        self.right_stick_x -= percent
    
    def action_right_stick_y_positive(self, percent: float, inverse: bool):
        self.right_stick_y += percent
    
    def action_right_stick_y_negative(self, percent: float, inverse: bool):
        self.right_stick_y -= percent
    
    def action_left_trigger(self, percent: float, inverse: bool):
        self.left_trigger_val = max(self.left_trigger_val, percent)
    
    def action_right_trigger(self, percent: float, inverse: bool):
        self.right_trigger_val = max(self.right_trigger_val, percent)
    
    # Button actions (pressed when analog > 50%)
    def action_button_a(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    
    def action_button_b(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    
    def action_button_x(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
    
    def action_button_y(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
    
    def action_left_bumper(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
    
    def action_right_bumper(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    
    def action_start(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
    
    def action_dpad_up(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
    
    def action_dpad_down(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
    
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
    
    def run(self):
        print("=" * 70)
        print("DrunkDeer -> Xbox Controller Emulator with Keyboard Suppression")
        print("=" * 70)
        
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
        
        # Load config (this also starts suppression)
        config_loaded = self.load_config()
        
        if not config_loaded:
            print("\n⚠ Using fallback configuration")
        
        print("\n✓ Virtual Xbox 360 controller created")
        print("\nPress Ctrl+C to stop")
        print("=" * 70 + "\n")
        
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
            print("\n\n" + "=" * 70)
            print("Stopping gracefully...")
            print("=" * 70)
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Stop keyboard suppression
            if self.suppressor:
                self.suppressor.stop()
                print("✓ Keyboard suppression stopped")
            
            if self.device:
                self.device.close()
                print("✓ Device closed")
            print("✓ Exited cleanly\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DrunkDeer to Xbox Controller Emulator with Keyboard Suppression"
    )
    parser.add_argument("--config", type=str, default="crew_motorfest_config.json",
                        help="Path to JSON config file")
    parser.add_argument("--deadzone-min", type=int, default=2)
    parser.add_argument("--deadzone-max", type=int, default=36)
    parser.add_argument("--poll-interval", type=int, default=5)
    
    args = parser.parse_args()
    
    controller = G75Controller(
        config_file=args.config,
        deadzone_min=args.deadzone_min,
        deadzone_max=args.deadzone_max,
        polling_interval_ms=args.poll_interval
    )
    
    controller.run()

if __name__ == "__main__":
    main()
