import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import sv_ttk
import threading
import json
import time
import os
import sys
import ctypes
import hid
import vgamepad as vg
from typing import Dict, Optional
import keyboard as kb

# Constants
VENDOR_ID = 0x352D
PRODUCT_ID = 0x2386
HID_USAGE = 0x0000
SETTINGS_FILE = "dd2rl.json"
DEFAULT_CONFIG_FILE = "config.json"


def is_admin():
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin():
    """Request admin elevation via UAC prompt"""
    if is_admin():
        return True
    
    try:
        # Get the script path
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script = sys.executable
            params = ""
        else:
            # Running as Python script - use pythonw.exe to avoid console
            python_exe = sys.executable
            if python_exe.lower().endswith('python.exe'):
                python_exe = python_exe[:-10] + 'pythonw.exe'
            
            script = python_exe
            params = f'"{os.path.abspath(sys.argv[0])}"'
        
        # Re-run the program with admin rights
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            script,
            params,
            None, 
            1  # SW_SHOWNORMAL
        )
        
        # ShellExecuteW returns a value > 32 on success
        if result > 32:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Admin elevation error: {e}")
        return False


def create_default_config():
    """Create a default config.json template"""
    default_config = {
        "game": "Example Game",
        "description": "Template configuration - customize for your game",
        "suppression": {
            "enabled": True,
            "toggle_key": "END",
            "description": "Press END to toggle keyboard suppression ON/OFF"
        },
        "controller_mappings": {
            "analog": {
                "Throttle": {
                    "drunkdeer_key": "W",
                    "controller": "RIGHT_TRIGGER",
                    "description": "Accelerate"
                },
                "Brake": {
                    "drunkdeer_key": "S",
                    "controller": "LEFT_TRIGGER",
                    "description": "Brake"
                },
                "SteerLeft": {
                    "drunkdeer_key": "A",
                    "controller": "LEFT_STICK_X_NEGATIVE",
                    "description": "Steer left"
                },
                "SteerRight": {
                    "drunkdeer_key": "D",
                    "controller": "LEFT_STICK_X_POSITIVE",
                    "description": "Steer right"
                }
            },
            "buttons": {
                "Action": {
                    "drunkdeer_key": "SPACE",
                    "controller": "A_BUTTON",
                    "description": "Primary action"
                },
                "Menu": {
                    "drunkdeer_key": "ESC",
                    "controller": "START_BUTTON",
                    "description": "Menu"
                }
            }
        }
    }
    
    with open(DEFAULT_CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=2)


class DrunkDeerController:
    def __init__(self):
        self.device: Optional[hid.device] = None
        self.gamepad: Optional[vg.VX360Gamepad] = None
        self.running = False
        self.controller_enabled = True
        self.suppression_enabled = False
        self.suppressed_keys = set()
        self.toggle_key = "f12"
        
        self.key_heights = [0] * 128
        self.config = {}
        self.key_name_to_index = self._build_key_map()
        
        self.deadzone_min = 2
        self.deadzone_max = 36
        self.poll_interval = 0.005
        
    def _build_key_map(self) -> Dict[str, int]:
        """Build keyboard layout mapping"""
        layout = [
            "u0", "ESC", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8",
            "F9", "F10", "F11", "F12", "PRTSCN", "INS", "DEL", "KP9", "u2", "u3", "u4", "u5",
            "SWUNG", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
            "MINUS", "PLUS", "BACK", "KP4", "HOME", "KP6", "u6", "u7", "u8", "u9",
            "TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
            "BRKTS_L", "BRKTS_R", "SLASH_K29", "KP1", "PGUP", "KP3", "u10", "u11", "u12", "u13",
            "CAPS", "A", "S", "D", "F", "G", "H", "J", "K", "L",
            "COLON", "QOTATN", "u14", "RETURN", "u15", "PGDN", "KP_DEL", "u16", "u17", "u18", "u19",
            "SHF_L", "EUR_K45", "Z", "X", "C", "V", "B", "N", "M",
            "COMMA", "PERIOD", "VIRGUE", "u20", "SHF_R", "ARR_UP", "u21", "NUMS", "u22", "u23", "u24", "u25",
            "END", "WIN_L", "ALT_L", "u26", "u27", "u28", "SPACE",
            "u29", "u30", "u31", "ALT_R", "FN1", "APP", "u32", "ARR_L",
            "ARR_DW", "ARR_R", "CTRL_R", "u33", "u34", "u35", "u36"
        ]
        return {name: idx for idx, name in enumerate(layout) if not name.startswith("u")}
    
    def load_config(self, config_path: str):
        """Load JSON configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        suppression_config = self.config.get('suppression', {})
        self.suppression_enabled = suppression_config.get('enabled', True)
        self.toggle_key = suppression_config.get('toggle_key', 'f12').lower()
    
    def open_device(self) -> bool:
        """Open HID device"""
        devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
        for dev in devices:
            if dev['usage_page'] == 0xFF00 and dev['usage'] == HID_USAGE:
                self.device = hid.device()
                self.device.open_path(dev['path'])
                self.device.set_nonblocking(False)
                return True
        return False
    
    def create_gamepad(self):
        """Create virtual Xbox 360 controller"""
        self.gamepad = vg.VX360Gamepad()
    
    def normalize_value(self, raw_value: int) -> float:
        """Normalize key height to 0-1 range with deadzone"""
        if raw_value < self.deadzone_min:
            return 0.0
        clamped = min(raw_value, self.deadzone_max)
        return clamped / 40.0
    
    def toggle_suppression(self):
        """Toggle keyboard suppression and controller state"""
        self.suppression_enabled = not self.suppression_enabled
        self.controller_enabled = self.suppression_enabled
        
        if not self.suppression_enabled:
            for key in list(self.suppressed_keys):
                try:
                    kb.unblock_key(key)
                except:
                    pass
            self.suppressed_keys.clear()
            
            if self.gamepad:
                self.gamepad.reset()
                self.gamepad.update()
        else:
            self._suppress_mapped_keys()
    
    def _suppress_mapped_keys(self):
        """Suppress all keys defined in the config mappings"""
        if not self.suppression_enabled:
            return
        
        for mapping in self.config.get('controller_mappings', {}).get('analog', {}).values():
            key_name = mapping.get('drunkdeer_key')
            if key_name:
                self._suppress_single_key(key_name)
        
        for mapping in self.config.get('controller_mappings', {}).get('buttons', {}).values():
            key_name = mapping.get('drunkdeer_key')
            if key_name:
                self._suppress_single_key(key_name)
    
    def _suppress_single_key(self, key_name: str):
        """Suppress a single keyboard key"""
        if not self.suppression_enabled:
            return
        
        try:
            kb_key = self._convert_key_name(key_name)
            if kb_key and kb_key not in self.suppressed_keys:
                kb.block_key(kb_key)
                self.suppressed_keys.add(kb_key)
        except Exception as e:
            pass
    
    def _convert_key_name(self, drunkdeer_key: str) -> Optional[str]:
        """Convert DrunkDeer key names to keyboard module format"""
        key_map = {
            'SHF_L': 'shift',
            'SHF_R': 'right shift',
            'CTRL_L': 'ctrl',
            'CTRL_R': 'right ctrl',
            'ALT_L': 'alt',
            'ALT_R': 'right alt',
            'WIN_L': 'win',
            'SPACE': 'space',
            'RETURN': 'enter',
            'BACK': 'backspace',
            'TAB': 'tab',
            'ESC': 'esc',
            'CAPS': 'caps lock',
            'APP': 'apps',
            'MINUS': '-',
            'PLUS': '=',
            'BRKTS_L': '[',
            'BRKTS_R': ']',
            'COLON': ';',
            'QOTATN': "'",
            'COMMA': ',',
            'PERIOD': '.',
            'VIRGUE': '/',
            'SLASH_K29': '\\',
            'SWUNG': '`',
            'INS': 'insert',
            'DEL': 'delete',
            'HOME': 'home',
            'END': 'end',
            'PGUP': 'page up',
            'PGDN': 'page down',
            'PRTSCN': 'print screen',
        }
        
        return key_map.get(drunkdeer_key, drunkdeer_key.lower())
    
    def process_mappings(self):
        """Process analog and button mappings"""
        if not self.controller_enabled or not self.gamepad:
            return
        
        analog_accum = {
            'LEFT_STICK_X': 0.0, 'LEFT_STICK_Y': 0.0,
            'RIGHT_STICK_X': 0.0, 'RIGHT_STICK_Y': 0.0,
            'LEFT_TRIGGER': 0.0, 'RIGHT_TRIGGER': 0.0
        }
        
        for mapping in self.config.get('controller_mappings', {}).get('analog', {}).values():
            key_idx = mapping.get('drunkdeer_index')
            if key_idx is None:
                key_name = mapping.get('drunkdeer_key')
                key_idx = self.key_name_to_index.get(key_name)
            
            if key_idx is None or key_idx >= len(self.key_heights):
                continue
            
            value = self.normalize_value(self.key_heights[key_idx])
            controller_action = mapping.get('controller', '')
            
            if 'LEFT_STICK_X_NEGATIVE' in controller_action:
                analog_accum['LEFT_STICK_X'] -= value
            elif 'LEFT_STICK_X_POSITIVE' in controller_action:
                analog_accum['LEFT_STICK_X'] += value
            elif 'LEFT_STICK_Y_NEGATIVE' in controller_action:
                analog_accum['LEFT_STICK_Y'] -= value
            elif 'LEFT_STICK_Y_POSITIVE' in controller_action:
                analog_accum['LEFT_STICK_Y'] += value
            elif 'RIGHT_STICK_X_NEGATIVE' in controller_action:
                analog_accum['RIGHT_STICK_X'] -= value
            elif 'RIGHT_STICK_X_POSITIVE' in controller_action:
                analog_accum['RIGHT_STICK_X'] += value
            elif 'RIGHT_STICK_Y_NEGATIVE' in controller_action:
                analog_accum['RIGHT_STICK_Y'] -= value
            elif 'RIGHT_STICK_Y_POSITIVE' in controller_action:
                analog_accum['RIGHT_STICK_Y'] += value
            elif 'LEFT_TRIGGER' in controller_action:
                analog_accum['LEFT_TRIGGER'] = max(analog_accum['LEFT_TRIGGER'], value)
            elif 'RIGHT_TRIGGER' in controller_action:
                analog_accum['RIGHT_TRIGGER'] = max(analog_accum['RIGHT_TRIGGER'], value)
        
        self.gamepad.left_joystick_float(
            max(-1.0, min(1.0, analog_accum['LEFT_STICK_X'])),
            max(-1.0, min(1.0, analog_accum['LEFT_STICK_Y']))
        )
        self.gamepad.right_joystick_float(
            max(-1.0, min(1.0, analog_accum['RIGHT_STICK_X'])),
            max(-1.0, min(1.0, analog_accum['RIGHT_STICK_Y']))
        )
        self.gamepad.left_trigger_float(max(0.0, min(1.0, analog_accum['LEFT_TRIGGER'])))
        self.gamepad.right_trigger_float(max(0.0, min(1.0, analog_accum['RIGHT_TRIGGER'])))
        
        button_map = {
            'A_BUTTON': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            'B_BUTTON': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            'X_BUTTON': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            'Y_BUTTON': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            'LEFT_BUMPER': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            'RIGHT_BUMPER': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            'START_BUTTON': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            'BACK_BUTTON': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            'LEFT_STICK_CLICK': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            'RIGHT_STICK_CLICK': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            'DPAD_UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            'DPAD_DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            'DPAD_LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            'DPAD_RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        }
        
        for mapping in self.config.get('controller_mappings', {}).get('buttons', {}).values():
            key_idx = mapping.get('drunkdeer_index')
            if key_idx is None:
                key_name = mapping.get('drunkdeer_key')
                key_idx = self.key_name_to_index.get(key_name)
            
            if key_idx is None or key_idx >= len(self.key_heights):
                continue
            
            value = self.normalize_value(self.key_heights[key_idx])
            controller_action = mapping.get('controller', '')
            
            if controller_action in button_map:
                if value > 0.5:
                    self.gamepad.press_button(button_map[controller_action])
                else:
                    self.gamepad.release_button(button_map[controller_action])
        
        self.gamepad.update()
    
    def run(self, log_callback):
        """Main loop"""
        self.running = True
        
        if not self.open_device():
            log_callback("ERROR: Could not open DrunkDeer keyboard")
            self.running = False
            return
        
        log_callback("✓ DrunkDeer keyboard connected")
        
        try:
            self.create_gamepad()
            log_callback("✓ Virtual Xbox 360 controller created")
        except Exception as e:
            log_callback(f"ERROR: Could not create controller: {e}")
            self.running = False
            return
        
        self.device.write([0x04, 0xa0, 0x02])
        time.sleep(0.1)
        self.device.read(65, timeout_ms=1000)
        
        self.controller_enabled = self.suppression_enabled
        if self.suppression_enabled:
            self._suppress_mapped_keys()
            log_callback("✓ Keyboard suppression enabled")
        
        status = "ON" if self.suppression_enabled else "OFF"
        log_callback(f"✓ Running - Suppression {status} (press {self.toggle_key.upper()} to toggle)")
        
        self.device.write([0x04, 0xb6, 0x03, 0x01])
        
        while self.running:
            try:
                data = self.device.read(65, timeout_ms=100)
                if not data or len(data) < 5:
                    continue
                
                if data[0] != 0x04 or data[1] != 0xb7:
                    continue
                
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
                    if idx >= len(self.key_heights):
                        continue
                    self.key_heights[idx] = data[i + 4] if (i + 4) < len(data) else 0
                
                if packet_type == 2:
                    self.process_mappings()
                    time.sleep(self.poll_interval)
                    self.device.write([0x04, 0xb6, 0x03, 0x01])
            
            except Exception as e:
                log_callback(f"ERROR: {e}")
                break
        
        for key in list(self.suppressed_keys):
            try:
                kb.unblock_key(key)
            except:
                pass
        self.suppressed_keys.clear()
        
        if self.gamepad:
            self.gamepad.reset()
            self.gamepad.update()
        if self.device:
            self.device.close()
        
        log_callback("Stopped")
    
    def stop(self):
        """Stop the controller"""
        self.running = False


class DrunkDeerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DrunkDeer G75 → Xbox Controller")
        self.root.geometry("900x700")
        
        self.controller = DrunkDeerController()
        self.controller_thread: Optional[threading.Thread] = None
        self.config_path = ""
        self.hotkey_registered = False
        
        self.setup_ui()
        self.check_default_config()
        
        # Check admin status
        if is_admin():
            self.log("✓ Running with Administrator privileges")
        else:
            self.log("⚠ Not running as Administrator - suppression may not work")
            self.log("  Click 'Request Admin' to restart with privileges")
        
        sv_ttk.set_theme("dark")
    
    def check_default_config(self):
        """Check for config.json in current directory"""
        if os.path.exists(DEFAULT_CONFIG_FILE):
            # Config exists, load it
            self.config_path = os.path.abspath(DEFAULT_CONFIG_FILE)
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, self.config_path)
            self.save_last_config()
            self.log(f"✓ Found and loaded: {DEFAULT_CONFIG_FILE}")
        else:
            # Config doesn't exist, create template
            try:
                create_default_config()
                self.log(f"⚠ config.json not found - created template")
                self.log("=" * 60)
                self.log("IMPORTANT: Customize config.json for your game!")
                self.log("")
                self.log("Options:")
                self.log("  1. Download the config from GitHub:")
                self.log("     https://github.com/TheX24/DD2RL/config.json")
                self.log("")
                self.log("  2. Edit config.json manually using DOCS.md")
                self.log("     as reference for key mappings")
                self.log("=" * 60)
                
                # Load the template
                self.config_path = os.path.abspath(DEFAULT_CONFIG_FILE)
                self.config_entry.delete(0, tk.END)
                self.config_entry.insert(0, self.config_path)
                self.save_last_config()
                
                # Show popup
                messagebox.showwarning(
                    "Config File Created",
                    "config.json was not found.\n\n"
                    "A template has been created for you.\n\n"
                    "Please customize it for your game:\n"
                    "• Download config from GitHub, or\n"
                    "• Edit config.json manually (see DOCS.md)\n\n"
                    "Check the log for more information."
                )
                
            except Exception as e:
                self.log(f"ERROR: Could not create config.json: {e}")
    
    def load_last_config(self):
        """Load the last used config file"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    last_config = settings.get('last_config')
                    if last_config and os.path.exists(last_config):
                        self.config_path = last_config
                        self.config_entry.delete(0, tk.END)
                        self.config_entry.insert(0, last_config)
                        self.log(f"Loaded last config: {last_config}")
        except Exception as e:
            self.log(f"Could not load last config: {e}")
    
    def save_last_config(self):
        """Save the current config path"""
        try:
            settings = {'last_config': self.config_path}
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            self.log(f"Could not save settings: {e}")
    
    def setup_ui(self):
        """Setup the GUI"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        title = ttk.Label(title_frame, text="DD2RL - DrunkDeer to Controller",
                         font=('Segoe UI', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        # Admin button
        if not is_admin():
            self.admin_btn = ttk.Button(title_frame, text="🛡 Request Admin", 
                                       command=self.request_admin_privileges, width=18)
            self.admin_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(config_frame, text="Config File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.config_entry = ttk.Entry(config_frame, width=50)
        self.config_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_config).grid(row=0, column=2, padx=(5, 0))
        
        control_frame = ttk.LabelFrame(main_frame, text="Control", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ Start", command=self.start_controller, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ Stop", command=self.stop_controller, 
                                   width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(status_frame, text="Controller:").pack(side=tk.LEFT, padx=(0, 5))
        self.controller_status = ttk.Label(status_frame, text="⚫ Disabled", foreground="gray")
        self.controller_status.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(status_frame, text="Suppression:").pack(side=tk.LEFT, padx=(0, 5))
        self.suppression_status = ttk.Label(status_frame, text="⚫ OFF", foreground="gray")
        self.suppression_status.pack(side=tk.LEFT)
        
        self.toggle_hint = ttk.Label(status_frame, text="(Press toggle key)", foreground="gray")
        self.toggle_hint.pack(side=tk.LEFT, padx=(10, 0))
        
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD, 
                                                  font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(settings_frame, text="Deadzone Min:").grid(row=0, column=0, sticky=tk.W)
        self.deadzone_min_var = tk.IntVar(value=2)
        ttk.Spinbox(settings_frame, from_=0, to=10, textvariable=self.deadzone_min_var, 
                   width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Deadzone Max:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.deadzone_max_var = tk.IntVar(value=36)
        ttk.Spinbox(settings_frame, from_=20, to=40, textvariable=self.deadzone_max_var, 
                   width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(settings_frame, text="Poll Interval (ms):").grid(row=0, column=4, sticky=tk.W, padx=(20, 0))
        self.poll_interval_var = tk.IntVar(value=5)
        ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.poll_interval_var, 
                   width=10).grid(row=0, column=5, padx=5)
    
    def request_admin_privileges(self):
        """Request admin elevation and restart"""
        result = request_admin()
        if result:
            # Successfully launched elevated process, exit this one
            self.root.quit()
            sys.exit(0)
        else:
            messagebox.showerror("Admin Elevation Failed", 
                               "Could not elevate privileges.\n\n"
                               "Try right-clicking the script and selecting 'Run as administrator'.")
    
    def setup_hotkeys(self):
        """Setup hotkey from config for toggling"""
        if self.hotkey_registered:
            try:
                kb.unhook_all()
            except:
                pass
        
        def on_toggle():
            if self.controller.running:
                self.controller.toggle_suppression()
                self.update_status_indicators()
                if self.controller.suppression_enabled:
                    self.log("✓ Controller ENABLED + Suppression ON")
                else:
                    self.log("⚠ Controller DISABLED + Suppression OFF")
        
        try:
            toggle_key = self.controller.toggle_key
            kb.on_press_key(toggle_key, lambda _: on_toggle(), suppress=False)
            self.hotkey_registered = True
            self.log(f"✓ Hotkey registered: {toggle_key.upper()}")
        except Exception as e:
            self.log(f"Warning: Hotkey setup failed: {e}")
            self.hotkey_registered = False
    
    def browse_config(self):
        """Browse for config file"""
        filename = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_path = filename
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, filename)
            self.save_last_config()
            self.log(f"Config loaded: {filename}")
    
    def log(self, message: str):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status_indicators(self):
        """Update status indicator labels"""
        if self.controller.controller_enabled:
            self.controller_status.config(text="🟢 Enabled", foreground="green")
        else:
            self.controller_status.config(text="🔴 Disabled", foreground="red")
        
        if self.controller.suppression_enabled:
            self.suppression_status.config(text="🟢 ON", foreground="green")
        else:
            self.suppression_status.config(text="🔴 OFF", foreground="red")
    
    def start_controller(self):
        """Start the controller"""
        if not self.config_path:
            messagebox.showerror("Error", "Please select a config file first")
            return
        
        try:
            self.controller.load_config(self.config_path)
            self.save_last_config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            return
        
        self.controller.deadzone_min = self.deadzone_min_var.get()
        self.controller.deadzone_max = self.deadzone_max_var.get()
        self.controller.poll_interval = self.poll_interval_var.get() / 1000.0
        
        self.toggle_hint.config(text=f"(Press {self.controller.toggle_key.upper()} to toggle)")
        
        self.setup_hotkeys()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log("Starting controller...")
        self.update_status_indicators()
        
        self.controller_thread = threading.Thread(
            target=self.controller.run,
            args=(self.log,),
            daemon=True
        )
        self.controller_thread.start()
    
    def stop_controller(self):
        """Stop the controller"""
        self.log("Stopping...")
        self.controller.stop()
        
        if self.controller_thread:
            self.controller_thread.join(timeout=2)
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.controller.controller_enabled = False
        self.controller.suppression_enabled = False
        self.update_status_indicators()
    
    def on_closing(self):
        """Handle window close"""
        if self.controller.running:
            self.stop_controller()
        
        try:
            kb.unhook_all()
        except:
            pass
        
        self.root.destroy()


def main():
    root = tk.Tk()
    app = DrunkDeerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
