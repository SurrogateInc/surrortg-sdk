"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Set to True if claw machine has Surrogate joystick splitter hardware
USE_JOYSTICK_SPLITTER = False
# Set to True if claw machine has Surrogate toy reset solenoid hardware
USE_TOY_RESET_SOLENOID = False
# Set to True if RPI has needed hardware to generate coin signal for claw
# machine and game is used in paid mode.
USE_COIN_GENERATOR = False
# Wait until something clears the toy from front of the toy sensor before
# starting new game.
BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED = True
# How long to wait after blocking toy has been removed
WAIT_TIME_AFTER_SENSOR_CLEARED = 10
# Maximum time for claw picking cycle and detecting toy
# (drop claw, lift claw, move claw and detect toy by sensor).
TOY_WAIT_TIME = 10
# Time for claw picking cycle (drop claw, lift claw and release)
CLAW_PICK_CYCLE_TIME = 7
# Time for claw to move from corner to corner (longest distance)
CLAW_CORNER_TO_CORNER_TIME = 2
# This constant must be set to the same value as claw machine game time.
# Set game time as long as claw machine allows.
CLAW_GAME_LENGTH = 60
# Time to wait between disabling player inputs and pressing claw button
STOP_TIME_BEFORE_BTN_PRESS = 0.25
# Claw needs to be moved right before game starts to start claw game timer.
# This constant defines how long claw is moved during that operation.
AUTOMATIC_MOVE_TIME = 0.25

# NOTE! This is a workaround because GE does not send max game length time
# This constant must be set to same value as GE game length
GE_GAME_LENGTH = 30

"""ClawButton"""
BTN_PIN = 21
BTN_TIME = 0.05

"""ClawJoystick"""
TOP_PIN = 5
LEFT_PIN = 8
BOTTOM_PIN = 7
RIGHT_PIN = 25
MIN_AMOUNT = 0.2
JOYSTICK_STATE_ON = 0
JOYSTICK_STATE_OFF = 1

"""ClawToySensor"""
TOY_SENSOR_PIN = 23
TOY_SENSOR_STATE_BLOCKED = 1

"""ClawCoinGenerator"""
# These configs are not used if coin generator is not enabled

# Pin for coin door signal
COIN_SIGNAL_PIN = 20

"""ClawJoystickSplitter"""
# These configs are not used if coin generator is not enabled

# Pin to disable physical joystick
JOYSTICK_DISABLE_PIN = 19

"""ClawSolenoid"""
# These configs are not used if toy reset solenoid system is not enabled

# Interval in seconds to fire solenoid if toy didn't fly out
SOLENOID_FIRE_INTERVAL = 5
# Pin to enable solenoid power supply
SOLENOID_PSU_PIN = 7
# Pin to fire solenoid
SOLENOID_FIRE_PIN = 4

# No effect, Arduino toy sensor is not supported currently
"""ClawArduinoToySensor"""
ARDUINO_PATH = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
BLOCKED_THRESHOLD = 25

# Override values in this file with those found in config_local.py
try:
    from games.claw.config_local import *  # noqa
except ModuleNotFoundError:
    pass
