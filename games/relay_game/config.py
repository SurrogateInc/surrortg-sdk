"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines name and pin number for the GPIO switch. Names are used in dashboard
# to identify player input and pin numbers are the Raspberry Pi BCM numbers.
GPIO_SWITCHES = {
    "switch_1": 26,
    "switch_2": 19,
    "switch_3": 13,
    "switch_4": 6,
}

"""GPIOSwitch"""
# Defines if GPIO ON level is HIGH or LOW
ON_LEVEL = "HIGH"

# Override values in this file with those found in config_local.py
try:
    from games.relay_game.config_local import *  # noqa
except ModuleNotFoundError:
    pass
