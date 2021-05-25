"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Correct row of options to the questions
AMOUNT_OF_PLAYERS = 10
CORRECT_ROW = ["c", "b", "c", "c", "c", "b", "a", "c", "a", "c"]

"""Servo"""
# Defines the Raspberry Pi GPIO pin number for the first servo
# The 9 other servos should be set to the next 9 pins
FIRST_SERVO_PIN = 12
SERVO_MIN_PULSE_WIDTH = 500
SERVO_MAX_PULSE_WIDTH = 2500
SERVO_MIN_FULL_SWEEP_TIME = 0.3
SERVO_ROTATION_UPDATE_FREQ = 30
# Angle that points the servo to the A, B or C option
# Servo is moved with 'rotate_to' function
# values should be between -1 and 1
A_ANGLE = 0.4
B_ANGLE = 0
C_ANGLE = -0.4
# Andle to put the servos to between questions
RESET_ANGLE = 1


# Override values in this file with those found in config_local.py
try:
    from games.trivia_game.config_local import *  # noqa
except ModuleNotFoundError:
    pass
