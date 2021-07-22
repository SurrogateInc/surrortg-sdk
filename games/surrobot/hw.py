import logging

import adafruit_ssd1306
import adafruit_tcs34725
import busio
from adafruit_motor import servo as AdafruitServo  # noqa:N812
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
from PIL import Image, ImageDraw

from games.surrobot.DRV8833 import DRV8833, DRV8833Motor, MotorController
from surrortg.devices import Servo, i2c_connected

# Motor driver control pins

# Front left motor
MOTOR_FL_IN_1 = 15
MOTOR_FL_IN_2 = 14
# Front right motor
MOTOR_FR_IN_1 = 17
MOTOR_FR_IN_2 = 27
# Rear right motor
MOTOR_RR_IN_1 = 5
MOTOR_RR_IN_2 = 6
# Rear left motor
MOTOR_RL_IN_1 = 26
MOTOR_RL_IN_2 = 19

FRONT_MOTORS_SLEEP = 4
REAR_MOTORS_SLEEP = 13

I2C_DEVICES = {
    "right oled": "0x3d",
    "left oled": "0x3c",
    "servo board": "0x40",
    "color sensor": "0x29",
}


class Hw:
    def __init__(self):
        for name, address in I2C_DEVICES.items():
            logging.info(
                f"{name} at {address} connected: {i2c_connected(address)}"
            )

        self.i2c = busio.I2C(SCL, SDA)
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = 50
        self.servos = []
        for i in range(16):
            servo = PCA9685Servo(AdafruitServo.Servo(self.pca.channels[i]))
            self.servos.append(servo)
        self.left_eye = Oled(self.i2c)
        self.right_eye = Oled(self.i2c, addr=0x3D)
        # These should be lazy generated?
        self.color_sensor = adafruit_tcs34725.TCS34725(self.i2c)
        self.color_sensor.active = False

        # Create motor drivers, one for front and one for rear
        self.motor_driver_front = DRV8833(
            ain1=MOTOR_FL_IN_1,
            ain2=MOTOR_FL_IN_2,
            bin1=MOTOR_FR_IN_1,
            bin2=MOTOR_FR_IN_2,
            sleep=FRONT_MOTORS_SLEEP,
        )
        self.motor_driver_rear = DRV8833(
            ain1=MOTOR_RR_IN_1,
            ain2=MOTOR_RR_IN_2,
            bin1=MOTOR_RL_IN_1,
            bin2=MOTOR_RL_IN_2,
            sleep=REAR_MOTORS_SLEEP,
        )

        # Create motor drivers for each 4 motor
        self.motor_fl = DRV8833Motor(
            drv8833=self.motor_driver_front, motor_number=1, direction="-"
        )
        self.motor_fr = DRV8833Motor(
            drv8833=self.motor_driver_front, motor_number=2, direction="-"
        )
        self.motor_rr = DRV8833Motor(
            drv8833=self.motor_driver_rear, motor_number=1, direction="-"
        )
        self.motor_rl = DRV8833Motor(
            drv8833=self.motor_driver_rear, motor_number=2, direction="-"
        )

        # Create motor controller for all 4 motors
        self.motor_controller = MotorController(
            self.motor_fl, self.motor_fr, self.motor_rr, self.motor_rl
        )

    def reset_eyes(self):
        self.left_eye.write("left eye")
        self.right_eye.write("right eye")


class Oled:
    def __init__(self, i2c, addr=0x3C):
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=addr)
        # Clear display.
        self.oled.fill(0)
        self.oled.show()
        self.last_text_writen = ""

    def write(self, text, x=0, y=0, fill=255):
        if text is not self.last_text_writen:
            image = Image.new("1", (self.oled.width, self.oled.height))
            draw = ImageDraw.Draw(image)
            draw.text((x, y), text, fill=fill)
            self.oled.image(image)
            self.oled.show()
            self.last_text_writen = text


class PCA9685Servo(Servo):
    def __init__(
        self,
        servo,
        min_pulse_width=500,
        max_pulse_width=2500,
        min_full_sweep_time=0.5,
        rotation_update_freq=25,
    ):
        """Simple to use servo class implemented with pigpio

        position property handles immediate position changes.
        rotation_speed property handles rotation with a spesific speed
        in the background.
        Also has rotate_to, detach and stop methods.

        :param pin: GPIO pin number
        :type pin: int
        :param min_pulse_width: between 500 and 2500, defaults to 500
        :type min_pulse_width: int, optional
        :param max_pulse_width: between 500 and 2500, defaults to 2500
        :type max_pulse_width: int, optional
        :param min_full_sweep_time: full sweep time in seconds,
            defaults to 0.5
        :type min_full_sweep_time: float, optional
        :param rotation_update_freq: rotation position update frequenzy,
            defaults to 25
        :type rotation_update_freq: int, optional
        :raises RuntimeError: If cannot connect to pigpio daemon
        """
        assert (
            500 <= min_pulse_width <= 2500
        ), "min_pulse_width should be between 500 and 2500"
        assert (
            500 <= max_pulse_width <= 2500
        ), "max_pulse_width should be between 500 and 2500"
        assert (
            min_pulse_width < max_pulse_width
        ), "min_pulse_width should be less than max_pulse_width"
        assert (
            min_full_sweep_time > 0
        ), "min_full_sweep_time should be positive"
        assert (
            rotation_update_freq > 0
        ), "rotation_update_freq should be positive"

        self._min_pulse_width = min_pulse_width
        self._max_pulse_width = max_pulse_width
        self._mid_pulse_width = (max_pulse_width + min_pulse_width) / 2
        self._max_pos_change_per_update = 2 / (
            rotation_update_freq * min_full_sweep_time
        )
        self._rotation_update_freq = rotation_update_freq
        self._latest_rotation_start_time = None
        self._position = None
        self._rotation_speed = 0
        self._stopped = False

        self.servo = servo

    def _set_position(self, position):
        scaled_pos = (
            -position * (self._mid_pulse_width - self._min_pulse_width)
            + self._mid_pulse_width
        )  # Scale -1 to 1 between min and max pulse width
        # self._pwm.set_servo_pulse(self._channel, int(scaled_pos))
        fraction = (scaled_pos - 500.0) / 2000.0
        self.servo.fraction = fraction
        self._position = position
