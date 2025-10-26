# Hardware Control Module

## Table of Contents
- [Components](#components)
  - [RFID Jammer (`rfid_jammer.py`)](#rfid-jammer-rfid_jammerpy)
  - [Catflap Controller (`catflap_controller.py`)](#catflap-controller-catflap_controllerpy)

Hardware interfaces for catflap control and camera management.

## Components

### RFID Jammer (`rfid_jammer.py`)
Controls a relay-switched RFID reader module to block the catflap's 134.2 kHz RFID reader.

**Hardware:**
- 134.2 kHz FDX-B RFID reader module
- 5V single-channel relay (active-low trigger)
- Connected to GPIO 26 on Raspberry Pi 5

**Functions:**
- `block_catflap()` - Activates RFID jammer (relay on)
- `unblock_catflap()` - Deactivates RFID jammer (relay off)

See [Hardware Setup Guide](../../../docs/HARDWARE_SETUP.md) for detailed assembly instructions.

### Catflap Controller (`catflap_controller.py`)
High-level async controller for catflap locking with timer management.

**Features:**
- Automatic unlock after configured duration (default: 300 seconds)
- Async lock/unlock operations with state tracking
- Detection pause integration during lock period

**Usage:**
```python
from catflap_prey_detector.hardware.catflap_controller import catflap_controller

# Lock the catflap
await catflap_controller.lock_catflap("Prey detected")

# Check status
status = catflap_controller.get_lock_status()

# Manual unlock
await catflap_controller.unlock_catflap("Manual override")
```

