"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Correct row of options to the questions
AMOUNT_OF_PLAYERS = 10
CORRECT_ROW = ["a", "a", "a", "a", "a", "a", "a", "a", "a", "a"]

"""Servo"""
# Defines the Raspberry Pi GPIO pin number for the first servo
# The 9 other servos should be set to the next 9 pins
FIRST_SERVO_PIN = 12
SERVO_MIN_PULSE_WIDTH = 500
SERVO_MAX_PULSE_WIDTH = 2500
SERVO_MIN_FULL_SWEEP_TIME = 0.3
SERVO_ROTATION_UPDATE_FREQ = 30


# Override values in this file with those found in config_local.py
try:
    from games.dog_feeder.config_local import *  # noqa
except ModuleNotFoundError:
    pass
