import asyncio
import logging
import time

import adafruit_ssd1306
import adafruit_tcs34725
import busio
from board import SCL, SDA
from PIL import Image, ImageDraw

from games.surrobot.DRV8833 import DRV8833, DRV8833Motor, MotorController
from surrortg.devices import Servo, i2c_connected

# Motor driver control pins

# Front left motor
MOTOR_FL_IN_1 = 22
MOTOR_FL_IN_2 = 23
# Front right motor
MOTOR_FR_IN_1 = 17
MOTOR_FR_IN_2 = 27
# Rear right motor
MOTOR_RR_IN_1 = 26
MOTOR_RR_IN_2 = 19
# Rear left motor
MOTOR_RL_IN_1 = 5
MOTOR_RL_IN_2 = 6

FRONT_MOTORS_SLEEP = 24
REAR_MOTORS_SLEEP = 13

SERVO_PINS = [21, 20, 16, 13, 12, 25]

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
        self.servos = [Servo(pin) for pin in SERVO_PINS]
        self.left_eye = Oled(self.i2c)
        self.right_eye = Oled(self.i2c, addr=0x3D)
        # These should be lazy generated?
        self.color_sensor = ColorSensor(self.i2c)

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
        self.left_eye.write("left eye")
        self.right_eye.write("right eye")

    def get_cpu_temperature(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_millidegrees = f.read()
            return int(temp_millidegrees) / 1000


class ColorSensor:
    def __init__(self, i2c, integration_time=150):
        self.working = False
        self.i2c = i2c
        self._integration_time = integration_time
        self._active = False
        self.safe_init()

    def safe_init(self):
        try:
            self.color_sensor = adafruit_tcs34725.TCS34725(self.i2c)
            self.color_sensor.integration_time = self._integration_time
            self.color_sensor.active = self._active
            self.working = True
        except (OSError, ValueError):
            logging.error("ColorSensor init failed")
            self.working = False

    @property
    def lux(self):
        # Try re-init if broken
        if not self.working:
            self.safe_init()
        # Try only if in a working state
        if self.working:
            try:
                return self.color_sensor.lux
            except OSError:
                logging.error("ColorSensor lux failed")
                self.working = False
                return None

    @property
    def active(self):
        # Try re-init if broken
        if not self.working:
            self.safe_init()
        # Try only if in a working state
        if self.working:
            try:
                return self.color_sensor.active
            except OSError:
                return None
        else:
            return None

    @active.setter
    def active(self, active):
        self._active = active
        # Try re-init if broken
        if not self.working:
            self.safe_init()
        # Try only if in a working state
        if self.working:
            try:
                self.color_sensor.active = self._active
            except OSError:
                pass


class Oled:
    def __init__(self, i2c, addr=0x3C, max_update_interval=0.5):
        self.working = False
        self.i2c = i2c
        self.addr = addr
        self.max_update_interval = max_update_interval
        self.last_update_ts = time.time()
        self.safe_init()
        self.last_text_writen = ""
        self.write_task = None

        # Show empty display if working
        if self.working:
            self.oled.fill(0)
            self.safe_show()

    def write(self, text, x=0, y=0, fill=255):
        if text is not self.last_text_writen:
            # Try re-init if broken
            if not self.working:
                self.safe_init()

            # Try writing only if in a working state
            if self.working:
                time_now = time.time()
                # Try writing now only if enough time has passed
                if time_now - self.last_update_ts > self.max_update_interval:
                    self.draw(text, x, y, fill)
                # If not, create a task to write later
                else:
                    if self.write_task is not None:
                        self.write_task.cancel()
                    wait_time = self.max_update_interval - (
                        time_now - self.last_update_ts
                    )
                    self.write_task = asyncio.create_task(
                        self.draw_after_wait(text, x, y, fill, wait_time)
                    )

    async def draw_after_wait(self, text, x, y, fill, wait_time):
        await asyncio.sleep(wait_time)
        self.draw(text, x, y, fill)

    def draw(self, text, x, y, fill):
        image = Image.new("1", (self.oled.width, self.oled.height))
        draw = ImageDraw.Draw(image)
        draw.text((x, y), text, fill=fill)
        self.oled.image(image)
        self.safe_show()
        self.last_text_writen = text
        self.last_update_ts = time.time()

    def safe_init(self):
        try:
            self.oled = adafruit_ssd1306.SSD1306_I2C(
                128, 64, self.i2c, addr=self.addr
            )
            self.working = True
        except (OSError, ValueError):
            logging.error(f"Oled init failed at address {hex(self.addr)}")
            self.working = False

    def safe_show(self):
        try:
            self.oled.show()
            self.working = True
        except OSError:
            logging.error(f"Oled show() failed at address {hex(self.addr)}")
            self.working = False
