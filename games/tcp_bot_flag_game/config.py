"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Servo"""
# Defines the Raspberry Pi GPIO pin number for the servo
SERVO_PIN = 2
SERVO_MIN_PULSE_WIDTH = 700
SERVO_MAX_PULSE_WIDTH = 2300
SERVO_MIN_FULL_SWEEP_TIME = 0.5
SERVO_ROTATION_UPDATE_FREQ = 30
SERVO_WAIT_BETWEEN_MOVE = 0.45


# Override values in this file with those found in config_local.py
try:
    from games.tcp_bot_flag_game.config_local import *  # noqa
except ModuleNotFoundError:
    pass
