import asyncio
import logging

from games.dog_feeder.config import (
    MAX_FEED_PER_GAME,
    SERVO_MAX_PULSE_WIDTH,
    SERVO_MIN_FULL_SWEEP_TIME,
    SERVO_MIN_PULSE_WIDTH,
    SERVO_PIN,
    SERVO_ROTATION_UPDATE_FREQ,
)
from surrortg import Game
from surrortg.devices import Servo
from surrortg.inputs import Joystick, Switch


class ServoSwitch(Switch):
    def __init__(self, servo, max_presses):
        self.servo = servo
        self.max_presses = max_presses
        self.reset_press_count()

    async def on(self, seat=0):
        logging.info("Switch on")
        self.press_count += 1
        if self.max_presses >= self.press_count:
            logging.info("Servo movement started")
            await self.servo.rotate_to(-1)
            await asyncio.sleep(0.1)
            await self.servo.rotate_to(1)
            logging.info("Servo movement ended")
        else:
            logging.info("Max press count reached")

    async def off(self, seat=0):
        logging.info("Switch off")

    def reset_press_count(self):
        self.press_count = 0


class DogFeederGame(Game):
    async def on_init(self):
        # Initialize input
        self.servo = Servo(
            SERVO_PIN,
            SERVO_MIN_PULSE_WIDTH,
            SERVO_MAX_PULSE_WIDTH,
            SERVO_MIN_FULL_SWEEP_TIME,
            SERVO_ROTATION_UPDATE_FREQ,
        )
        await self.servo.rotate_to(1)
        self.servo_switch = ServoSwitch(self.servo, MAX_FEED_PER_GAME)

        # Register input
        self.io.register_inputs({"feed": self.servo_switch})

    async def on_pre_game(self):
        # Reset servo to center
        await self.servo.rotate_to(1)
        self.servo_switch.reset_press_count()

    async def on_start(self):
        logging.info("Game starts")

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()


if __name__ == "__main__":
    # Start running the game
    DogFeederGame().run()
