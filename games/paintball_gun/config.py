"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines name and pin number for the trigger switch. Pin number is the
# Raspberry Pi BCM number.
TRIGGER_PIN = 26
# Defines the maximum amount of trigger presses per turn
MAX_TRIGGER_PRESSES = 1
# Defines the maximum game time. The game will end at latest after this time.
MAX_GAME_TIME = 30

"""TriggerSwitch"""
# Defines if GPIO ON level is HIGH or LOW
ON_LEVEL = "LOW"

# If either of these settings is set, every round must be started manually
# by host. Dashboard setting waits until 'start' button is pressed on
# admin dashboard. Keyboard setting waits until 'Enter' is pressed on keyboard
# attached to RPI. Both of these settings cannot be set at the same time.
WAIT_CONTINUE_DASHBOARD = False
WAIT_CONTINUE_KEYBOARD = True

if WAIT_CONTINUE_KEYBOARD and WAIT_CONTINUE_DASHBOARD:
    raise ValueError("Game should continue either from dashboard or keyboard.")

# Override values in this file with those found in config_local.py
try:
    from games.relay_game.config_local import *  # noqa
except ModuleNotFoundError:
    pass
