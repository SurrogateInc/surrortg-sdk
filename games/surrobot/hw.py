import logging

import busio
from board import SCL, SDA

from games.surrobot.DRV8833 import DRV8833, DRV8833Motor, MotorController
from surrortg.devices import SafeTCS34725, Servo, i2c_connected
from surrortg.devices.oled import Oled

# Motor driver control pins
# Front left motor
MOTOR_FL_IN_1 = 16
MOTOR_FL_IN_2 = 20
# Front right motor
MOTOR_FR_IN_1 = 26
MOTOR_FR_IN_2 = 21
# Rear right motor
MOTOR_RR_IN_1 = 19
MOTOR_RR_IN_2 = 13
# Rear left motor
MOTOR_RL_IN_1 = 6
MOTOR_RL_IN_2 = 12

SERVO_PINS = [17, 27, 22, 25, 24, 23, 5, 18]

I2C_DEVICES = {
    "right oled": "0x3d",
    "left oled": "0x3c",
    "color sensor": "0x29",
}

OLED_UPDATE_INTERVAL = 0.5


class Hw:
    def __init__(self):
        for name, address in I2C_DEVICES.items():
            logging.info(
                f"{name} at {address} connected: {i2c_connected(address)}"
            )

        self.i2c = busio.I2C(SCL, SDA)
        self.servos = [Servo(pin) for pin in SERVO_PINS]
        self.left_eye = Oled(
            self.i2c, max_update_interval=OLED_UPDATE_INTERVAL
        )
        self.right_eye = Oled(
            self.i2c, addr=0x3D, max_update_interval=OLED_UPDATE_INTERVAL
        )
        # These should be lazy generated?
        self.color_sensor = SafeTCS34725(self.i2c)
        self.color_sensor.integration_time = 150
        self.color_sensor.active = False

        # Create motor drivers, one for front and one for rear motors
        self.motor_driver_front = DRV8833(
            ain1=MOTOR_FL_IN_1,
            ain2=MOTOR_FL_IN_2,
            bin1=MOTOR_FR_IN_1,
            bin2=MOTOR_FR_IN_2,
        )
        self.motor_driver_rear = DRV8833(
            ain1=MOTOR_RR_IN_1,
            ain2=MOTOR_RR_IN_2,
            bin1=MOTOR_RL_IN_1,
            bin2=MOTOR_RL_IN_2,
        )

        # Abstract motor drivers into 4 individual motors
        self.motor_fl = DRV8833Motor(
            drv8833=self.motor_driver_front, motor_number=1, direction="-"
        )
        self.motor_fr = DRV8833Motor(
            drv8833=self.motor_driver_front, motor_number=2, direction="-"
        )
        self.motor_rr = DRV8833Motor(
            drv8833=self.motor_driver_rear, motor_number=1, direction="+"
        )
        self.motor_rl = DRV8833Motor(
            drv8833=self.motor_driver_rear, motor_number=2, direction="+"
        )

        # Create motor controller for all 4 motors
        self.motor_controller = MotorController(
            self.motor_fl, self.motor_fr, self.motor_rr, self.motor_rl
        )

    def reset_eyes(self):
        self.left_eye.show_text("left eye")
        self.right_eye.show_text("right eye")

    def get_cpu_temperature(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_millidegrees = f.read()
            return int(temp_millidegrees) / 1000
