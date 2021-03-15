"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

# Reset Trinket board each game loop
RESET_TRINKET_EACH_LOOP = False

"""TrinketResetSwitch"""
# Pin to reset Trinket
TRINKET_RESET_PIN = 23

# Override values in this file with those found in config_local.py
try:
    from games.ninswitch.config_local import *  # noqa
except ModuleNotFoundError:
    pass
