# DD2RL (DrunkDeer to Roller)

Use your DrunkDeer G75 magnetic keyboard as a virtual Xbox 360 controller for games with analog steering, triggers, and camera control.

## Features

- Analog input from key travel distance
- Virtual Xbox 360 controller via ViGEm
- JSON-based config profiles per game
- Optional keyboard suppression with toggle key
- Configurable deadzones and polling interval

## Requirements

- Windows
- DrunkDeer G75
- ViGEmBus driver: install from official ViGEmBus releases

Run the script as Administrator if you want keyboard suppression to work.

## Quick Start

1. Run the app

2. Click Browse to select your config JSON file

3. Click Start to enable the controller

4. Press F12 to toggle between:
   - OFF = Keyboard mode (controller disabled)
   - ON = Controller mode (keyboard suppressed)

5. Click Stop when done

## Toggle Mode Explained

The F12 key acts as a program switch:

Suppression OFF (Red):
- Keyboard inputs work normally
- Virtual controller is DISABLED
- Game sees keyboard only

Suppression ON (Green):
- Keyboard inputs are blocked
- Virtual controller is ENABLED
- Game sees controller only

## Command Line Usage (Optional)

```bash
python DD2RL.pyw --config my_game.json
```
Options:
```bash
  --config FILE         Config JSON file
  --deadzone-min N      Minimum travel threshold (default: 2)
  --deadzone-max N      Maximum travel for 100% (default: 36)
  --poll-interval N     Update interval in ms (default: 5)
```
## Troubleshooting

No controller in game:
  - Install ViGEmBus driver
  - Restart PC
  - Check "Set up USB game controllers" in Windows

Keyboard suppression fails:
  - Run as Administrator
  - Some keys (arrows) may not be fully suppressible

Key not working:
  - Check key name spelling (case-sensitive)
  - ESC is at index 1, not 0
  - Arrow keys need drunkdeer_index
  - Check console/GUI log for errors

Analog too sensitive/insensitive:
  - Adjust Deadzone Max (lower = more sensitive)
  - Adjust Deadzone Min (higher = less sensitive)

For config documentation see the wiki\
Made by my beloved Claude Sonnet 4.5