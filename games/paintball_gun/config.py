"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines the Raspberry Pi GPIO pin number for the trigger switch.
TRIGGER_PIN = 14
# Defines the maximum amount of trigger presses per turn
MAX_TRIGGER_PRESSES = 1

"""TriggerSwitch"""
# Defines if GPIO ON level is LOW
ON_LEVEL_LOW = True

# Override values in this file with those found in config_local.py
try:
    from games.paintball_gun.config_local import *  # noqa
except ModuleNotFoundError:
    pass
