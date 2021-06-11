"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines the Raspberry Pi GPIO pin number for the relay switches.
PINS = {
    "left": 26,
    "right": 19,
    "forward": 13,
    "back": 6,
}

"""RelaySwitch"""
# Defines if GPIO ON level is LOW
ON_LEVEL_LOW = True

# Override values in this file with those found in config_local.py
try:
    from games.roomba_driver.config_local import *  # noqa
except ModuleNotFoundError:
    pass
