import logging

from surrortg import Game
from surrortg.devices import Servo
from surrortg.inputs import Joystick

GPIO_PIN = 17  # servo control wire pin number
SPEED_ADJUST = 1.0  # set this between 0.0 and 1.0


class ServoJoystick(Joystick):
    def __init__(self):
        logging.info("Creating Servo")
        self.servo = Servo(GPIO_PIN)

    async def handle_coordinates(self, x, y, seat=0):
        x *= SPEED_ADJUST
        logging.info(f"Setting Servo rotation speed to: {x:.2f}")
        self.servo.rotation_speed = x

    async def reset(self, seat=0):
        logging.info("Resetting Servo to the middle")
        self.servo.position = 0

    async def shutdown(self, seat):
        logging.info("Stopping Servo")
        self.servo.stop()


class ServoGame(Game):
    async def on_init(self):
        logging.info("Creating and registering ServoJoystick Input")
        self.io.register_inputs({"joystick_main": ServoJoystick()})


ServoGame().run()
