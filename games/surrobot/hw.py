import asyncio
import logging
import time

import adafruit_ssd1306
import busio
from board import SCL, SDA
from PIL import Image, ImageDraw

from games.surrobot.DRV8833 import DRV8833, DRV8833Motor, MotorController
from surrortg.devices import SafeTCS34725, Servo, i2c_connected

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
        self.left_eye.write("left eye")
        self.right_eye.write("right eye")

    def get_cpu_temperature(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_millidegrees = f.read()
            return int(temp_millidegrees) / 1000


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
