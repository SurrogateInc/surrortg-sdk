import logging

from games.fortune_wheel.config import (
    SERVO_MAX_PULSE_WIDTH,
    SERVO_MIN_FULL_SWEEP_TIME,
    SERVO_MIN_PULSE_WIDTH,
    SERVO_PIN,
    SERVO_ROTATION_UPDATE_FREQ,
)
from surrortg import Game
from surrortg.devices import Servo
from surrortg.inputs import Switch


class ServoSwitch(Switch):
    def __init__(self, servo, stop_cb):
        self.servo = servo
        self.stop_cb = stop_cb

    async def on(self, seat=0):
        logging.info("Switch on")
        logging.info("Servo movement started")
        await self.servo.rotate_to(-1)
        logging.info("Servo movement ended")
        self.stop_cb()

    async def off(self, seat=0):
        logging.info("Switch off")


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
        await self.servo.rotate_to(-1)
        self.servo_switch = ServoSwitch(self.servo, self.stop_cb)

        # Register input
        self.io.register_inputs({"stop": self.servo_switch})

    async def on_pre_game(self):
        # Reset servo to center
        await self.servo.rotate_to(-1)
        await self.servo.rotate_to(1)

    async def on_prepare(self):
        # If you return false the game will not start automatically
        # The game needs to be started from admin panel
        # This is ideal for games that need manual reset before
        # approving the start
        return False

    async def on_start(self):
        logging.info("Game starts")

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()

    def stop_cb(self):
        # After user stops the wheel we end the game
        # The score type is "Total Games"
        # Send score 1 to count as valid game
        self.io.send_score(score=1, final_score=True)


if __name__ == "__main__":
    # Start running the game
    DogFeederGame().run()
