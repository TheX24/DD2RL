"""
DEBUG VERSION - Shows detailed logging for index 119 (LEFT arrow)
"""

import hid
import time
import vgamepad as vg
from dataclasses import dataclass
from typing import Callable, Dict, Set
import json
import sys
import os
import keyboard

VENDOR_ID = 0x352D
PRODUCT_ID = 0x2386
HID_USAGE = 0x0000

@dataclass
class KeyAction:
    function: Callable
    inverse: bool = False
    description: str = ""

class KeyboardSuppressor:
    def __init__(self, suppress_keys: Set[str], toggle_key: str = "f12"):
        self.suppress_keys = suppress_keys
        self.toggle_key = toggle_key.lower()
        self.suppression_active = True
        self.hooked = False
        
    def start(self):
        try:
            for key in self.suppress_keys:
                keyboard.block_key(key)
                print(f"   Blocking: {key}")
            keyboard.add_hotkey(self.toggle_key, self.toggle_suppression, suppress=False)
            self.hooked = True
            status = "ON" if self.suppression_active else "OFF"
            print(f"\n🔒 Keyboard suppression: {status}")
        except Exception as e:
            print(f"\n⚠ Keyboard suppression failed: {e}")
            self.hooked = False
    
    def toggle_suppression(self):
        self.suppression_active = not self.suppression_active
        if self.suppression_active:
            for key in self.suppress_keys:
                keyboard.block_key(key)
            print(f"\n🔒 Keyboard suppression: ON")
        else:
            for key in self.suppress_keys:
                keyboard.unblock_key(key)
            print(f"\n🔓 Keyboard suppression: OFF")
    
    def stop(self):
        if self.hooked:
            try:
                for key in self.suppress_keys:
                    keyboard.unblock_key(key)
                keyboard.remove_hotkey(self.toggle_key)
            except:
                pass

class G75Controller:
    def __init__(self, config_file="crew_motorfest_config_test_nosuppress_arrows.json", deadzone_min=2, deadzone_max=36, polling_interval_ms=5):
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
        
        self.left_stick_x = 0.0
        self.left_stick_y = 0.0
        self.right_stick_x = 0.0
        self.right_stick_y = 0.0
        self.left_trigger_val = 0.0
        self.right_trigger_val = 0.0
        
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
        
        self.drunkdeer_to_standard = {
            "W": "w", "A": "a", "S": "s", "D": "d",
            "E": "e", "R": "r", "F": "f", "T": "t",
            "Q": "q", "Z": "z", "X": "x", "C": "c",
            "V": "v", "B": "b", "H": "h", "N": "n",
            "P": "p", "M": "m",
            "SPACE": "space", "SHF_L": "shift", "SHF_R": "shift",
            "ARR_L": "down", "ARR_R": "right", "ARR_UP": "up", "ARR_DW": "right",
            "ESC": "esc", "TAB": "tab", "RETURN": "enter"
        }
    
    def load_config(self):
        if not os.path.exists(self.config_file):
            print(f"⚠ Config file '{self.config_file}' not found.")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            game_name = config.get('game', 'Unknown')
            print(f"\n📋 Loading config for: {game_name}")
            
            suppression_config = config.get('suppression', {})
            toggle_key = suppression_config.get('toggle_key', 'f12')
            enable_suppression = suppression_config.get('enabled', True)
            
            suppress_keys = set()
            
            analog_maps = config.get('controller_mappings', {}).get('analog', {})
            for action, mapping in analog_maps.items():
                if 'drunkdeer_index' in mapping:
                    keycode = mapping['drunkdeer_index']
                    key_name = f"Index{keycode}"
                else:
                    key_name = mapping['drunkdeer_key']
                    try:
                        keycode = self.keyboard_layout.index(key_name)
                    except ValueError:
                        print(f"  ⚠ Key '{key_name}' not found in layout")
                        continue
                
                controller_action = mapping['controller']
                description = mapping.get('description', action)
                
                # Skip suppression for arrow keys if suppress=False
                if mapping.get('suppress', True):
                    standard_key = self.drunkdeer_to_standard.get(mapping.get('drunkdeer_key', ''), 'unknown')
                    if standard_key != 'unknown':
                        suppress_keys.add(standard_key)
                
                if 'LEFT_STICK_X_POSITIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_left_stick_x_positive, description=description)
                elif 'LEFT_STICK_X_NEGATIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_left_stick_x_negative, description=description)
                elif 'LEFT_STICK_Y_POSITIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_left_stick_y_positive, description=description)
                elif 'LEFT_STICK_Y_NEGATIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_left_stick_y_negative, description=description)
                elif 'RIGHT_STICK_X_POSITIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_right_stick_x_positive, description=description)
                elif 'RIGHT_STICK_X_NEGATIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_right_stick_x_negative, description=description)
                elif 'RIGHT_STICK_Y_POSITIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_right_stick_y_positive, description=description)
                elif 'RIGHT_STICK_Y_NEGATIVE' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_right_stick_y_negative, description=description)
                elif 'RIGHT_TRIGGER' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_right_trigger, description=description)
                elif 'LEFT_TRIGGER' in controller_action:
                    self.register_key_action_by_index(keycode, self.action_left_trigger, description=description)
            
            button_maps = config.get('controller_mappings', {}).get('buttons', {})
            for action, mapping in button_maps.items():
                key_name = mapping['drunkdeer_key']
                controller_button = mapping['controller']
                description = mapping.get('description', action)
                
                standard_key = self.drunkdeer_to_standard.get(key_name, key_name.lower())
                suppress_keys.add(standard_key)
                
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
                elif 'BACK' in controller_button:
                    self.register_key_action(key_name, self.action_back, description=description)
                elif 'LEFT_STICK_CLICK' in controller_button:
                    self.register_key_action(key_name, self.action_left_stick_click, description=description)
                elif 'RIGHT_STICK_CLICK' in controller_button:
                    self.register_key_action(key_name, self.action_right_stick_click, description=description)
                elif 'DPAD_UP' in controller_button:
                    self.register_key_action(key_name, self.action_dpad_up, description=description)
                elif 'DPAD_DOWN' in controller_button:
                    self.register_key_action(key_name, self.action_dpad_down, description=description)
                elif 'DPAD_LEFT' in controller_button:
                    self.register_key_action(key_name, self.action_dpad_left, description=description)
                elif 'DPAD_RIGHT' in controller_button:
                    self.register_key_action(key_name, self.action_dpad_right, description=description)
            
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
        else:
            print(f"✓ Connected to DrunkDeer keyboard")
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
    
    def register_key_action_by_index(self, keycode: int, action_func: Callable, inverse: bool = False, description: str = ""):
        self.key_action_map[keycode] = KeyAction(action_func, inverse, description)
        key_name = self.keyboard_layout[keycode] if keycode < len(self.keyboard_layout) else f"Index{keycode}"
        print(f"  ✓ Index {keycode:3d} ({key_name:8s}) -> {description}")
    
    def register_key_action(self, key_name: str, action_func: Callable, inverse: bool = False, description: str = ""):
        try:
            keycode = self.keyboard_layout.index(key_name)
            self.key_action_map[keycode] = KeyAction(action_func, inverse, description)
            print(f"  ✓ {key_name:8s} -> {description}")
        except ValueError:
            print(f"  ⚠ Key '{key_name}' not found in layout")
    
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
        # DEBUG: Log when index 119 (LEFT arrow) is pressed
        if percent > 0:
            print(f"DEBUG: RIGHT_STICK_X_NEGATIVE triggered! percent={percent:.2f}")
    def action_right_stick_y_positive(self, percent: float, inverse: bool):
        self.right_stick_y += percent
    def action_right_stick_y_negative(self, percent: float, inverse: bool):
        self.right_stick_y -= percent
    def action_left_trigger(self, percent: float, inverse: bool):
        self.left_trigger_val = max(self.left_trigger_val, percent)
    def action_right_trigger(self, percent: float, inverse: bool):
        self.right_trigger_val = max(self.right_trigger_val, percent)
    
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
    def action_back(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
    def action_left_stick_click(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
    def action_right_stick_click(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
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
    def action_dpad_left(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
    def action_dpad_right(self, percent: float, inverse: bool):
        if percent > 0.5:
            self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        else:
            self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
    
    def process_key_height(self, keycode: int, travel_percent: float):
        # DEBUG: Log index 119 specifically
        if keycode == 119:
            print(f"\nDEBUG: Index 119 (LEFT arrow) detected! travel={travel_percent:.2f}")
        
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
            
            # DEBUG: Log packet type 2 buffer for index 119
            if packet_type == 2 and keynum == 119 and new_value > 0:
                print(f"\nDEBUG PACKET 2: Index 119 raw={raw_value}, deadzone={new_value}, percent={percent:.2f}")
            
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
        print("DEBUG VERSION - Will log index 119 (LEFT arrow) activity")
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
        config_loaded = self.load_config()
        if not config_loaded:
            print("\n⚠ Config file not found")
            return
        print("\n✓ Virtual Xbox 360 controller created")
        print("\nPress LEFT arrow and watch for DEBUG messages")
        print("Press Ctrl+C to stop")
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
        except KeyboardInterrupt:
            print("\n\nStopping...")
        finally:
            if self.suppressor:
                self.suppressor.stop()
            if self.device:
                self.device.close()
            print("Exited\n")

def main():
    controller = G75Controller(config_file="crew_motorfest_config_test_nosuppress_arrows.json")
    controller.run()

if __name__ == "__main__":
    main()
