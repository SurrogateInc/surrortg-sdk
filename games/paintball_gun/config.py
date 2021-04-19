"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines name and pin number for the trigger switch. Pin number is the
# Raspberry Pi BCM number.
TRIGGER_PIN = 14
# Defines the maximum amount of trigger presses per turn
MAX_TRIGGER_PRESSES = 1

"""TriggerSwitch"""
# Defines if GPIO ON level is HIGH or LOW
ON_LEVEL = "LOW"

# Override values in this file with those found in config_local.py
try:
    from games.relay_game.config_local import *  # noqa
except ModuleNotFoundError:
    pass
