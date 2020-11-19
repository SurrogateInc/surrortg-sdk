"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
ABSOLUTE_GAME_MAX_TIME = 50
TOY_WAIT_TIME = 10
USE_INTERNAL_IR_SENSOR = True
JOYSTICK_DISABLE_PIN = 19
STOP_TIME_BEFORE_BTN_PRESS = 0.25
AUTOMATIC_MOVE_TIME = 0.25
WAIT_TIME_AFTER_SENSOR_BLOCKED = 10
BLOCKED_SENSOR_PING_TIME = 5
BLOCK_GAME_LOOP_IF_SENSOR_STUCK = True

"""ClawInternalToySensor"""
IR_SENSOR_PIN = 23
TOYSENSOR_STATE_ON = 1

"""ClawToySensor"""
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

# Override values in this file with those found in config_local.py
try:
    from games.claw.config_local import *  # noqa
except ModuleNotFoundError:
    pass
