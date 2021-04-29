"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines the maximum amount of times dogs can be fed per game
MAX_FEED_PER_GAME = 2

"""Servo"""
# Defines the Raspberry Pi GPIO pin number for the servo
SERVO_PIN = 12
SERVO_MIN_PULSE_WIDTH = 1500
SERVO_MAX_PULSE_WIDTH = 1800
SERVO_MIN_FULL_SWEEP_TIME = 0.15
SERVO_ROTATION_UPDATE_FREQ = 50


# Override values in this file with those found in config_local.py
try:
    from games.dog_feeder.config_local import *  # noqa
except ModuleNotFoundError:
    pass
