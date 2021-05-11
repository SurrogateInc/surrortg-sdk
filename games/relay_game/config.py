"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines name and pin number for the relay switch. Names are used in dashboard
# to identify player input and pin numbers are the Raspberry Pi GPIO numbers.
RELAY_SWITCHES = {
    "switch_1": 26,
    "switch_2": 19,
    "switch_3": 13,
    "switch_4": 6,
}

"""RelaySwitch"""
# Defines if Relay GPIO ON level is LOW
ON_LEVEL_LOW = False

# Override values in this file with those found in config_local.py
try:
    from games.relay_game.config_local import *  # noqa
except ModuleNotFoundError:
    pass
