"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
AMOUNT_OF_PLAYERS = 10
# Correct row of options (answers) to the questions
# Note: All separate options need to have angle set in 'OPTION_ANGLES'
CORRECT_ROW = ["c", "b", "c", "c", "c", "b", "a", "c", "a", "c"]

"""Servo"""
# Defines the Raspberry Pi GPIO pin number for the first servo
# The 9 other servos should be set to the next 9 pins
FIRST_SERVO_PIN = 12
SERVO_MIN_PULSE_WIDTH = 500
SERVO_MAX_PULSE_WIDTH = 2500
SERVO_MIN_FULL_SWEEP_TIME = 0.3
SERVO_ROTATION_UPDATE_FREQ = 30
# Angle that points the servo to the a, b or c option
# Servo is moved with 'rotate_to' function
# values should be between -1 and 1
# Note: You can add more options than just a, b, c
OPTION_ANGLES = {
    "a": 0.4,
    "b": 0,
    "c": -0.4,
}
# Angle to put the servos to between questions
RESET_ANGLE = 1


# Override values in this file with those found in config_local.py
try:
    from games.trivia_game.config_local import *  # noqa
except ModuleNotFoundError:
    pass
