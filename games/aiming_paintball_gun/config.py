"""
DO NOT MODIFY THE VALUES FROM THIS FILE
TO OVERRIDE THESE VALUES, USE config_local.py
"""

"""Game"""
# Defines the maximum amount of trigger presses per turn
MAX_TRIGGER_PRESSES = 3

"""TriggerSwitch"""
# Defines the Raspberry Pi GPIO pin number for the trigger switch
TRIGGER_PIN = 14
# Defines if GPIO ON level is HIGH or LOW
ON_LEVEL = "LOW"

"""Servo"""
# Defines the Raspberry Pi GPIO pin number for the servo
SERVO_PIN = 12
SERVO_MIN_PULSE_WIDTH = 1400
SERVO_MAX_PULSE_WIDTH = 1650
SERVO_MIN_FULL_SWEEP_TIME = 0.5
SERVO_ROTATION_UPDATE_FREQ = 150


# Override values in this file with those found in config_local.py
try:
    from games.aiming_paintball_gun.config_local import *  # noqa
except ModuleNotFoundError:
    pass
