"""
DrunkDeer G75 Device Diagnostic Tool
Helps identify why the keyboard isn't being detected
"""

import hid

print("=" * 70)
print("DrunkDeer G75 HID Device Diagnostic")
print("=" * 70)

# Known DrunkDeer identifiers
VENDOR_ID = 0x352D
KNOWN_PRODUCT_IDS = {
    0x2382: "A75",
    0x2383: "A75/A75 Pro", 
    0x2384: "G75"
}

print("\nSearching for ALL HID devices from DrunkDeer (Vendor ID: 0x352D)...")
print("-" * 70)

all_drunkdeer = hid.enumerate(VENDOR_ID, 0x0)

if not all_drunkdeer:
    print("❌ No DrunkDeer devices found at all!")
    print("\nTroubleshooting steps:")
    print("  1. Make sure the keyboard is plugged in")
    print("  2. Try a different USB port")
    print("  3. Replug the keyboard")
    print("  4. Check Windows Device Manager for any driver issues")
    print("  5. Try running as Administrator")
else:
    print(f"✓ Found {len(all_drunkdeer)} DrunkDeer HID interface(s):\n")
    
    for idx, dev in enumerate(all_drunkdeer):
        product_name = KNOWN_PRODUCT_IDS.get(dev['product_id'], "Unknown")
        
        print(f"Device #{idx + 1}:")
        print(f"  Product: {product_name} (PID: 0x{dev['product_id']:04X})")
        print(f"  Path: {dev['path']}")
        print(f"  Usage Page: 0x{dev['usage_page']:04X}")
        print(f"  Usage: 0x{dev['usage']:04X}")
        print(f"  Interface: {dev['interface_number']}")
        
        if dev['usage'] == 0x0:
            print(f"  ✓ This interface has usage=0x0 (CORRECT for raw data)")
        else:
            print(f"  ⚠ This interface has usage=0x{dev['usage']:04X} (NOT the raw data interface)")
        
        print()

print("-" * 70)
print("\nSearching specifically for G75 (PID: 0x2384) with usage=0x0...")
print("-" * 70)

g75_devices = hid.enumerate(VENDOR_ID, 0x2384)
g75_correct = [d for d in g75_devices if d['usage'] == 0x0]

if g75_correct:
    print(f"✓ Found {len(g75_correct)} G75 device(s) with correct usage!")
    for dev in g75_correct:
        print(f"  Path: {dev['path']}")
        print("  → This device SHOULD work with the script")
else:
    print("❌ No G75 devices found with usage=0x0")
    print("\nPossible solutions:")
    print("  1. Your keyboard might be A75/A75 Pro instead of G75")
    print("  2. Try changing PRODUCT_ID in the script:")
    print("     - For A75: use 0x2382 or 0x2383")
    print("     - For G75: use 0x2384")

print("\n" + "=" * 70)
print("Recommendation:")
print("=" * 70)

all_dd = hid.enumerate(VENDOR_ID, 0x0)
correct_usage = [d for d in all_dd if d['usage'] == 0x0]

if correct_usage:
    dev = correct_usage[0]
    print(f"\nUse this in your script:")
    print(f"  VENDOR_ID = 0x{VENDOR_ID:04X}")
    print(f"  PRODUCT_ID = 0x{dev['product_id']:04X}  # {KNOWN_PRODUCT_IDS.get(dev['product_id'], 'Unknown model')}")
    print(f"  HID_USAGE = 0x{dev['usage']:04X}")
else:
    print("\n⚠ Could not find a suitable device")

print()
