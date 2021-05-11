"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Servo"""
# Defines the Raspberry Pi GPIO pin number for the servo
SERVO_PIN = 12
SERVO_MIN_PULSE_WIDTH = 1200
SERVO_MAX_PULSE_WIDTH = 2100
SERVO_MIN_FULL_SWEEP_TIME = 0.15
SERVO_ROTATION_UPDATE_FREQ = 50


# Override values in this file with those found in config_local.py
try:
    from games.fortune_wheel.config_local import *  # noqa
except ModuleNotFoundError:
    pass
