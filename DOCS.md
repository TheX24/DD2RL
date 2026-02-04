# DrunkDeer G75 to Xbox Controller - Complete Documentation

## 1. Architecture

The script:
1. Opens DrunkDeer keyboard as HID device
2. Reads key height values (0-40) from HID packets
3. Normalizes and applies deadzones (0-1 range)
4. Controls virtual Xbox 360 controller via ViGEm
5. Optionally suppresses keyboard inputs

HID Packet Layout:
- Packet 0: key indices 0-58
- Packet 1: key indices 59-117
- Packet 2: key indices 118-125 (arrow cluster)

## 2. JSON Config Structure

```json
{
  "game": "Game Name",
  "description": "Profile description",
  "suppression": {
    "enabled": true,
    "toggle_key": "f12"
  },
  "controller_mappings": {
    "analog": { },
    "buttons": { }
  }
}
```

### 2.1 Suppression

- enabled: true/false
- toggle_key: key name for toggling (e.g. "f12")

## 3. Analog Mappings

### 3.1 By Key Name

```json
"Throttle": {
  "drunkdeer_key": "W",
  "controller": "RIGHT_TRIGGER",
  "description": "Accelerate"
}
```


### 3.2 By Index (for arrow keys)

```json
"CameraLeft": {
  "drunkdeer_index": 119,
  "controller": "RIGHT_STICK_X_NEGATIVE",
  "description": "Look Left"
}
```

Arrow key indices for DrunkDeer G75:
- 98: UP arrow
- 119: LEFT arrow
- 120: DOWN arrow
- 121: RIGHT arrow

### 3.3 Valid Controller Actions (Analog)

Left Stick:
- LEFT_STICK_X_POSITIVE (right)
- LEFT_STICK_X_NEGATIVE (left)
- LEFT_STICK_Y_POSITIVE (down)
- LEFT_STICK_Y_NEGATIVE (up)

Right Stick:
- RIGHT_STICK_X_POSITIVE (right)
- RIGHT_STICK_X_NEGATIVE (left)
- RIGHT_STICK_Y_POSITIVE (down)
- RIGHT_STICK_Y_NEGATIVE (up)

Triggers:
- LEFT_TRIGGER
- RIGHT_TRIGGER

### 3.4 Multiple Keys to Same Analog

Multiple keys can map to same analog - values add up and clamp to [-1,1] for sticks or [0,1] for triggers.

## 4. Button Mappings

```json
"Handbrake": {
  "drunkdeer_key": "SPACE",
  "controller": "X_BUTTON",
  "description": "Handbrake"
}
```

### 4.1 Valid Controller Actions (Buttons)

- A_BUTTON, B_BUTTON, X_BUTTON, Y_BUTTON
- LEFT_BUMPER, RIGHT_BUMPER
- START_BUTTON, BACK_BUTTON
- LEFT_STICK_CLICK, RIGHT_STICK_CLICK
- DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT

Activation: >50% key travel

## 5. DrunkDeer Key Names
## Standard Keys (Use with drunkdeer_key)

| Index | Key Name    | Description           | JSON Usage |
|-------|-------------|-----------------------|------------|
| 0     | (empty)     | Not usable            | - |
| 1     | ESC         | Escape                | "drunkdeer_key": "ESC" |
| 2     | F1          | Function 1            | "drunkdeer_key": "F1" |
| 3     | F2          | Function 2            | "drunkdeer_key": "F2" |
| 4     | F3          | Function 3            | "drunkdeer_key": "F3" |
| 5     | F4          | Function 4            | "drunkdeer_key": "F4" |
| 6     | F5          | Function 5            | "drunkdeer_key": "F5" |
| 7     | F6          | Function 6            | "drunkdeer_key": "F6" |
| 8     | F7          | Function 7            | "drunkdeer_key": "F7" |
| 9     | F8          | Function 8            | "drunkdeer_key": "F8" |
| 10    | F9          | Function 9            | "drunkdeer_key": "F9" |
| 11    | F10         | Function 10           | "drunkdeer_key": "F10" |
| 12    | F11         | Function 11           | "drunkdeer_key": "F11" |
| 13    | F12         | Function 12           | "drunkdeer_key": "F12" |
| 14    | PRTSCN      | Print Screen          | "drunkdeer_key": "PRTSCN" |
| 15    | INS         | Insert                | "drunkdeer_key": "INS" |
| 16    | DEL         | Delete                | "drunkdeer_key": "DEL" |
| 17    | KP9         | Numpad 9              | "drunkdeer_key": "KP9" |
| 18-21 | u1-u4     | Undefined             | Not usable
| 22    | SWUNG       | Tilde (~)             | "drunkdeer_key": "SWUNG" |
| 23    | 1           | Number 1              | "drunkdeer_key": "1" |
| 24    | 2           | Number 2              | "drunkdeer_key": "2" |
| 25    | 3           | Number 3              | "drunkdeer_key": "3" |
| 26    | 4           | Number 4              | "drunkdeer_key": "4" |
| 27    | 5           | Number 5              | "drunkdeer_key": "5" |
| 28    | 6           | Number 6              | "drunkdeer_key": "6" |
| 29    | 7           | Number 7              | "drunkdeer_key": "7" |
| 30    | 8           | Number 8              | "drunkdeer_key": "8" |
| 31    | 9           | Number 9              | "drunkdeer_key": "9" |
| 32    | 0           | Number 0              | "drunkdeer_key": "0" |
| 33    | MINUS       | Minus (-)             | "drunkdeer_key": "MINUS" |
| 34    | PLUS        | Equals (=)            | "drunkdeer_key": "PLUS" |
| 35    | BACK        | Backspace             | "drunkdeer_key": "BACK" |
| 36    | KP4         | Numpad 4              | "drunkdeer_key": "KP4" |
| 37    | HOME        | Home                  | "drunkdeer_key": "HOME" |
| 38    | KP6         | Numpad 6              | "drunkdeer_key": "KP6" |
| 39-42 | u5-u8     | Undefined             | Not usable |
| 43    | TAB         | Tab                   | "drunkdeer_key": "TAB" |
| 44    | Q           | Q                     | "drunkdeer_key": "Q" |
| 45    | W           | W                     | "drunkdeer_key": "W" |
| 46    | E           | E                     | "drunkdeer_key": "E" |
| 47    | R           | R                     | "drunkdeer_key": "R" |
| 48    | T           | T                     | "drunkdeer_key": "T" |
| 49    | Y           | Y                     | "drunkdeer_key": "Y" |
| 50    | U           | U                     | "drunkdeer_key": "U" |
| 51    | I           | I                     | "drunkdeer_key": "I" |
| 52    | O           | O                     | "drunkdeer_key": "O" |
| 53    | P           | P                     | "drunkdeer_key": "P" |
| 54    | BRKTS_L     | Left Bracket [        | "drunkdeer_key": "BRKTS_L" |
| 55    | BRKTS_R     | Right Bracket ]       | "drunkdeer_key": "BRKTS_R" |
| 56    | SLASH_K29   | Backslash \           | "drunkdeer_key": "SLASH_K29" |
| 57    | KP1         | Numpad 1              | "drunkdeer_key": "KP1" |
| 58    | PGUP        | Page Up               | "drunkdeer_key": "PGUP" |
| 59    | KP3         | Numpad 3              | "drunkdeer_key": "KP3" |
| 60-63 | u9-u12    | Undefined             | Not usable |
| 64    | CAPS        | Caps Lock             | "drunkdeer_key": "CAPS" |
| 65    | A           | A                     | "drunkdeer_key": "A" |
| 66    | S           | S                     | "drunkdeer_key": "S" |
| 67    | D           | D                     | "drunkdeer_key": "D" |
| 68    | F           | F                     | "drunkdeer_key": "F" |
| 69    | G           | G                     | "drunkdeer_key": "G" |
| 70    | H           | H                     | "drunkdeer_key": "H" |
| 71    | J           | J                     | "drunkdeer_key": "J" |
| 72    | K           | K                     | "drunkdeer_key": "K" |
| 73    | L           | L                     | "drunkdeer_key": "L" |
| 74    | COLON       | Semicolon (;)         | "drunkdeer_key": "COLON" |
| 75    | QOTATN      | Quote (')             | "drunkdeer_key": "QOTATN" |
| 76    | u13         | Undefined             | Not usable |
| 77    | RETURN      | Enter                 | "drunkdeer_key": "RETURN" |
| 78    | u14         | Undefined             | Not usable |
| 79    | PGDN        | Page Down             | "drunkdeer_key": "PGDN" |
| 80    | KP_DEL      | Numpad Decimal        | "drunkdeer_key": "KP_DEL" |
| 81-84 | u15-u18   | Undefined             | Not usable |
| 85    | SHF_L       | Left Shift            | "drunkdeer_key": "SHF_L" |
| 86    | EUR_K45     | ISO Key               | "drunkdeer_key": "EUR_K45" |
| 87    | Z           | Z                     | "drunkdeer_key": "Z" |
| 88    | X           | X                     | "drunkdeer_key": "X" |
| 89    | C           | C                     | "drunkdeer_key": "C" |
| 90    | V           | V                     | "drunkdeer_key": "V" |
| 91    | B           | B                     | "drunkdeer_key": "B" |
| 92    | N           | N                     | "drunkdeer_key": "N" |
| 93    | M           | M                     | "drunkdeer_key": "M" |
| 94    | COMMA       | Comma (,)             | "drunkdeer_key": "COMMA" |
| 95    | PERIOD      | Period (.)            | "drunkdeer_key": "PERIOD" |
| 96    | VIRGUE      | Slash (/)             | "drunkdeer_key": "VIRGUE"
| 97    | u19         | Undefined             | Not usable |
| 98    | SHF_R       | Right Shift / UP ⚠️   | "drunkdeer_index": 98 |
| 99    | ARR_UP      | Arrow Label           | "drunkdeer_key": "ARR_UP" |
|100    | u20         | Undefined             | Not usable |
|101    | NUMS        | Num Lock              | "drunkdeer_key": "NUMS" |
|102-105 | u21-u24 | Undefined             | Not usable |
|106    | END         | End                   | "drunkdeer_key": "END" |
|107    | WIN_L       | Windows               | "drunkdeer_key": "WIN_L" |
|108    | ALT_L       | Left Alt              | "drunkdeer_key": "ALT_L" |
|109-111 | u25-u27 | Undefined             | Not usable |
|112    | SPACE       | Spacebar              | "drunkdeer_key": "SPACE" |
|113-115 | u28-u30 | Undefined             | Not usable |
|116    | ALT_R       | Right Alt             | "drunkdeer_key": "ALT_R" |
|117    | FN1         | Function              | "drunkdeer_key": "FN1" |
|118    | APP         | Menu                  | "drunkdeer_key": "APP" |
|119    | (empty)     | Physical LEFT ⚠️      | "drunkdeer_index": 119 |
|120    | ARR_L       | Arrow Label / DOWN ⚠️ | "drunkdeer_index": 120 |
|121    | ARR_DW      | Arrow Label / RIGHT ⚠️| "drunkdeer_index": 121 |
|122    | ARR_R       | Arrow Label           | "drunkdeer_key": "ARR_R" |
|123    | CTRL_R      | Right Control         | "drunkdeer_key": "CTRL_R" |
|124-127 | u31-u34 | Undefined             | Not usable |

SUMMARY:
- Total: 128 positions
- Usable: 91 keys
- Undefined: 34 keys (u1-u34)
- Empty: 3 slots

### QUICK REFERENCE
Letters: A=65, B=91, C=89, D=67, E=46, F=68, G=69, H=70, I=51, J=71, 
         K=72, L=73, M=93, N=92, O=52, P=53, Q=44, R=47, S=66, T=48, 
         U=50, V=90, W=45, X=88, Y=49, Z=87

Numbers: 0=32, 1=23, 2=24, 3=25, 4=26, 5=27, 6=28, 7=29, 8=30, 9=31

Navigation: INS=15, DEL=16, HOME=37, END=106, PGUP=58, PGDN=79

Arrows (use index): UP=98, LEFT=119, DOWN=120, RIGHT=121

## 6. Advanced Configuration

### Deadzone Configuration

Deadzone Min (default: 2):
- Values below this = 0
- Higher value = less sensitive

Deadzone Max (default: 36):
- Values above this = 100%
- Lower value = more sensitive

Poll Interval (default: 5ms):
- Update rate = 1000 / interval
- Default = 200Hz

### GUI Settings
Adjust in real-time through the GUI:
- Deadzone Min: 0-10
- Deadzone Max: 20-40
- Poll Interval: 1-20ms

### Keyboard Suppression

When enabled:
- Blocks keyboard inputs from reaching the game
- Only controller inputs work
- Press F12 to toggle

Requirements:
- Run as Administrator
- Arrow keys may not be fully suppressible

Toggle Mode:
- Suppression OFF = Keyboard mode (controller disabled)
- Suppression ON = Controller mode (keyboard suppressed)

### Combining Analog Inputs

Sticks: values accumulate, clamped to [-1,1]
Triggers: maximum value among all mapped keys, clamped to [0,1]

## 7. Complete Examples

### Racing Game (The Crew Motorfest)

```json
{
  "game": "The Crew Motorfest",
  "suppression": {
    "enabled": true,
    "toggle_key": "f12"
  },
  "controller_mappings": {
    "analog": {
      "Throttle": {
        "drunkdeer_key": "W",
        "controller": "RIGHT_TRIGGER"
      },
      "Brake": {
        "drunkdeer_key": "S",
        "controller": "LEFT_TRIGGER"
      },
      "SteerLeft": {
        "drunkdeer_key": "A",
        "controller": "LEFT_STICK_X_NEGATIVE"
      },
      "SteerRight": {
        "drunkdeer_key": "D",
        "controller": "LEFT_STICK_X_POSITIVE"
      },
      "CameraLeft": {
        "drunkdeer_index": 119,
        "controller": "RIGHT_STICK_X_NEGATIVE"
      },
      "CameraRight": {
        "drunkdeer_index": 121,
        "controller": "RIGHT_STICK_X_POSITIVE"
      },
      "CameraUp": {
        "drunkdeer_index": 98,
        "controller": "RIGHT_STICK_Y_POSITIVE"
      },
      "CameraDown": {
        "drunkdeer_index": 120,
        "controller": "RIGHT_STICK_Y_NEGATIVE"
      }
    },
    "buttons": {
      "Nitro": {
        "drunkdeer_key": "SHF_L",
        "controller": "A_BUTTON"
      },
      "Handbrake": {
        "drunkdeer_key": "SPACE",
        "controller": "X_BUTTON"
      },
      "Reset": {
        "drunkdeer_key": "R",
        "controller": "Y_BUTTON"
      },
      "ShiftUp": {
        "drunkdeer_key": "E",
        "controller": "RIGHT_BUMPER"
      },
      "ShiftDown": {
        "drunkdeer_key": "Q",
        "controller": "LEFT_BUMPER"
      },
      "Horn": {
        "drunkdeer_key": "H",
        "controller": "RIGHT_STICK_CLICK"
      },
      "Assistant": {
        "drunkdeer_key": "C",
        "controller": "DPAD_UP"
      },
      "Camera": {
        "drunkdeer_key": "V",
        "controller": "DPAD_DOWN"
      },
      "Photo": {
        "drunkdeer_key": "P",
        "controller": "DPAD_RIGHT"
      },
      "Menu": {
        "drunkdeer_key": "ESC",
        "controller": "START_BUTTON"
      }
    }
  }
}
```

### Third-Person Action Game

```json
{
  "game": "Action Game",
  "suppression": { 
    "enabled": true, 
    "toggle_key": "f12" 
  },
  "controller_mappings": {
    "analog": {
      "MoveForward": {
        "drunkdeer_key": "W",
        "controller": "LEFT_STICK_Y_NEGATIVE"
      },
      "MoveBack": {
        "drunkdeer_key": "S",
        "controller": "LEFT_STICK_Y_POSITIVE"
      },
      "MoveLeft": {
        "drunkdeer_key": "A",
        "controller": "LEFT_STICK_X_NEGATIVE"
      },
      "MoveRight": {
        "drunkdeer_key": "D",
        "controller": "LEFT_STICK_X_POSITIVE"
      },
      "CameraUp": {
        "drunkdeer_key": "I",
        "controller": "RIGHT_STICK_Y_POSITIVE"
      },
      "CameraDown": {
        "drunkdeer_key": "K",
        "controller": "RIGHT_STICK_Y_NEGATIVE"
      },
      "CameraLeft": {
        "drunkdeer_key": "J",
        "controller": "RIGHT_STICK_X_NEGATIVE"
      },
      "CameraRight": {
        "drunkdeer_key": "L",
        "controller": "RIGHT_STICK_X_POSITIVE"
      }
    },
    "buttons": {
      "Jump": {
        "drunkdeer_key": "SPACE",
        "controller": "A_BUTTON"
      },
      "Dodge": {
        "drunkdeer_key": "SHF_L",
        "controller": "B_BUTTON"
      },
      "Attack": {
        "drunkdeer_key": "E",
        "controller": "X_BUTTON"
      },
      "Heavy": {
        "drunkdeer_key": "R",
        "controller": "Y_BUTTON"
      },
      "LockOn": {
        "drunkdeer_key": "F",
        "controller": "RIGHT_STICK_CLICK"
      },
      "Interact": {
        "drunkdeer_key": "Q",
        "controller": "LEFT_BUMPER"
      },
      "Item": {
        "drunkdeer_key": "T",
        "controller": "RIGHT_BUMPER"
      },
      "Menu": {
        "drunkdeer_key": "ESC",
        "controller": "START_BUTTON" 
      },
      "Map": { 
        "drunkdeer_key": "TAB", 
        "controller": "BACK_BUTTON" 
      }
    }
  }
}
```

### 2D Platformer

```json
{
  "game": "Platformer",
  "suppression": {
    "enabled": true,
    "toggle_key": "f12"
  },
  "controller_mappings": {
    "analog": {
      "MoveLeft": {
        "drunkdeer_key": "A",
        "controller": "LEFT_STICK_X_NEGATIVE"
      },
      "MoveRight": {
        "drunkdeer_key": "D",
        "controller": "LEFT_STICK_X_POSITIVE"
      }
    },
    "buttons": {
      "Jump": {
        "drunkdeer_key": "SPACE",
        "controller": "A_BUTTON"
      },
      "Attack": {
        "drunkdeer_key": "E",
        "controller": "X_BUTTON"
      },
      "Dash": {
        "drunkdeer_key": "SHF_L",
        "controller": "B_BUTTON"
      },
      "Special": {
        "drunkdeer_key": "Q",
        "controller": "Y_BUTTON"
      },
      "Menu": {
        "drunkdeer_key": "ESC",
        "controller": "START_BUTTON"
      }
    }
  }
}
```

## 8. Troubleshooting

### Device Not Found
- Check USB connection
- Unplug and reconnect keyboard
- Verify keyboard works (type in notepad)
- Make sure that you have got a keyboard that is supported
- Make sure that the web driver is completely closed

### Keyboard Suppression Fails
- Run as Administrator (most common)
- Some keys cannot be suppressed (arrow cluster)
- Disable antivirus temporarily

### Controller Not Detected
- Install ViGEmBus driver
- Restart PC
- Check "Set up USB game controllers" in Windows

### Keys Not Responding
- Check JSON for typos (case-sensitive)
- Verify key names match layout
- Check console for error messages

### Analog Too Sensitive/Insensitive
Adjust deadzones:
- More sensitive: --deadzone-max 30
- Less sensitive: --deadzone-max 40
- Higher activation: --deadzone-min 5

### Double Inputs (Keyboard + Controller)
- Enable keyboard suppression
- Run as Administrator
- For arrow keys: disable keyboard controls in-game

## 9. Technical Details

### Key Travel Processing
1. Raw HID value: 0-40
2. Apply deadzone_min threshold
3. Clamp to deadzone_max
4. Normalize to 0-1 (divide by 40)
5. Send to virtual controller

### Frame Update Cycle
1. Read HID packet
2. Process key heights
3. Accumulate analog values
4. On packet type 2:
   - Clamp and send to controller
   - Reset accumulator
   - Wait polling_interval_ms
   - Request next packet

### Supported Keyboards
- DrunkDeer G75 (tested)
- Other keyboards may work but are not tested

## 10. CLI Reference

```bash
python DD2RL.py [options]
```

Options:
  --config FILE         Config JSON file (default: config.json)
  --deadzone-min N      Minimum travel threshold (default: 2)
  --deadzone-max N      Maximum travel for 100% (default: 36)
  --poll-interval N     Update interval in ms (default: 5)

Examples:
```bash
python DD2RL.py
python DD2RL.py --config my_game.json
python DD2RL.py --deadzone-min 3 --deadzone-max 35
python DD2RL.py --poll-interval 8
```
