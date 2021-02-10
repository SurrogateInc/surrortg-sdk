"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
USE_INTERNAL_TOY_SENSOR = True
# set True if claw machine has Surrogate joystick splitter
USE_JOYSTICK_SPLITTER = False
# set True if claw machine has Surrogate toy reset solenoid
USE_TOY_RESET_SOLENOID = False
# set true if claw machine needs coins to start game
USE_COIN_SIGNAL_GENERATOR = False
# wait until something clears toy from front of the toy sensor
BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED = True
# how often toy sensor is pinged when sensor is blocked
BLOCKED_SENSOR_PING_INTERVAL = 1
# how long to wait after blocking toy has been removed
WAIT_TIME_AFTER_SENSOR_CLEARED = 10
# maximum time for claw picking cycle and detecting toy
# (drop claw, lift claw, move claw and detect toy by sensor)
TOY_WAIT_TIME = 10
# time for claw picking cycle
# (drop claw, lift claw and release)
CLAW_PICK_CYCLE_TIME = 7
# time for claw to move from corner to corner (longest distance)
CLAW_CORNER_TO_CORNER_TIME = 2
# this constant must be set to same value as claw machine game time
# set game time as long as claw machine allows
CLAW_GAME_LENGTH = 60
# time to wait between disabling player inputs and pressing claw button
STOP_TIME_BEFORE_BTN_PRESS = 0.25
# claw needs to be moved right before game starts to start claw game timer
# this constant defines how long claw is moved during that operation
AUTOMATIC_MOVE_TIME = 0.25

# pin for Surrogate joystick splitter
JOYSTICK_DISABLE_PIN = 19

# pin for coin door signal
COIN_SIGNAL_PIN = 20

# NOTE! This is a workaround because GE does not send max game length time
# This constant must be set to same value as GE game length
GE_GAME_LENGTH = 30

"""ClawToySensor"""
TOY_SENSOR_PIN = 23
TOY_SENSOR_STATE_BLOCKED = 1

"""ClawArduinoToySensor"""
ARDUINO_PATH = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
BLOCKED_THRESHOLD = 25

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

"""ClawSolenoid"""
# interval in seconds to fire solenoid if toy didn't fly out
SOLENOID_FIRE_INTERVAL = 5
# pin to enable solenoid power supply
SOLENOID_PSU_PIN = 7
# pin to fire solenoid
SOLENOID_FIRE_PIN = 4

# override values in this file with those found in config_local.py
try:
    from games.claw.config_local import *  # noqa
except ModuleNotFoundError:
    pass
