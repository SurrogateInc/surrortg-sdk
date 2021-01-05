"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

from enum import Enum, auto


class GameModes(Enum):
    PAID = auto()
    FREE = auto()


# Generic
MAX_BLINKING_START_WAIT_DURING_INIT = 15
MAX_BLINKING_START_WAIT_DURING_PREPARE = 60
GAME_MODE = GameModes.PAID
MAX_INPUTS_PER_INPUT = 6
PER_SECONDS = 1

# Buttons
LEFT_FLIPPER_PIN = 5
RIGHT_FLIPPER_PINS = [7, 9]
START_BUTTON_PIN = 8
SERVICE_CREDIT_BUTTON_PIN = 25
MAGNET_BUTTON_SLAM_TILT_PIN = 11

BUTTON_PRESS_TIME = 0.3
MAX_HOLD_TIME = 75

ABUSE_SLEEP = 10

# Plunger
PLUNGER_PIN = 21
BALL_SENSOR_PIN = 22
START_BUTTON_LED_PIN = 23
PLUNGER_PRESS_TIME = 0.2
PLUNGER_MIN_FREQ = 5
AUTO_PLUNGE_TIME = 10
# if set to false, ball count might be wrong
# but it is ok if the game state is not tied to ball_counter
WAIT_FOR_BALL_SAVE = False
BALL_SAVE_PLUNGE_TIME = 2

# Start button light
REQUIRED_BLINKING_TIME = 8
MAX_BLINKING_INTERVAL = 1.5
REQUIRED_TIME_TO_REGISTER_STATE = 2

assert (
    MAX_BLINKING_START_WAIT_DURING_INIT > REQUIRED_BLINKING_TIME
), "will never detect blinking during init"
assert (
    MAX_BLINKING_START_WAIT_DURING_PREPARE > REQUIRED_BLINKING_TIME
), "might not detect blinking during prepare"

# Override values in this file with those found in config_local.py
try:
    from games.arcade_pinball.config_local import *  # noqa
except ModuleNotFoundError:
    pass
