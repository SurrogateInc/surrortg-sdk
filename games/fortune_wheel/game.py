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

"""
This game implementation was used as a part of 7.5.2021
fortune wheel event at surrogate.tv.

The fortune wheel hardware included a servo attached to a
wood block that could stop the wheel from spinning.
Config in config.py are set so that the Servo function
`rotate_to(1)` will move the stopper up so that the wheel
can freely spin. `rotate_to(-1)` on the other hand will move
the stopper down so that the wheel will stop.
"""


class ServoSwitch(Switch):
    """
    ServoSwitch class stops the wheel on user action.
    It assumes that the given `servo` is setup so that calling
    `servo.rotate_to(-1)` will make the wheel stop.

    It also has `stop_cp` that is called after servo is moved down.
    """

    def __init__(self, servo, stop_cb):
        self.servo = servo
        self.stop_cb = stop_cb

    async def on(self, seat=0):
        logging.info("Switch on")
        logging.info("Servo moving down")
        await self.servo.rotate_to(-1)
        logging.info("Servo movement ended")
        self.stop_cb()

    async def off(self, seat=0):
        logging.info("Switch off")


class FortuneWheelGame(Game):
    """FortuneWheelGame implements the basic game loop.

    It will move the stopper up before game starts and
    ends the game after user has moved the stopper back
    down.
    """

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
        # You can bind this input to a key or mobile button
        # from the admin panel.
        self.io.register_inputs({"stop": self.servo_switch})

    async def on_prepare(self):
        # If you return false the game will not start automatically
        # The game needs to be started from admin panel
        # This is ideal for games that need manual reset before
        # approving the start
        return False

    async def on_pre_game(self):
        # Moving the servo up so that the wheel can be spun
        logging.info("Servo moving up")
        await self.servo.rotate_to(1)

    async def on_start(self):
        logging.info("Game started")

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()

    def stop_cb(self):
        # After user stops the wheel we end the game
        # The score type is set to "Total Games" on admin panel
        # Send score 1 to count as valid game
        self.io.send_score(score=1, final_score=True)


if __name__ == "__main__":
    # Start running the game
    FortuneWheelGame().run()
