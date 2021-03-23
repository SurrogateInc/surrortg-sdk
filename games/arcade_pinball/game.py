import asyncio
import logging

import pigpio

from games.arcade_pinball.arcade_button import ArcadeButton, ArcadeMultiButton
from games.arcade_pinball.config import (
    ABUSE_SLEEP,
    BALL_SENSOR_PIN,
    GAME_MODE,
    LEFT_FLIPPER_PIN,
    MAGNET_BUTTON_SLAM_TILT_PIN,
    MAX_BLINKING_START_WAIT_DURING_INIT,
    MAX_BLINKING_START_WAIT_DURING_PREPARE,
    PLUNGER_PIN,
    RIGHT_FLIPPER_PINS,
    SERVICE_CREDIT_BUTTON_PIN,
    START_BUTTON_LED_PIN,
    START_BUTTON_PIN,
    GameModes,
)
from games.arcade_pinball.plunger import Plunger
from games.arcade_pinball.start_led import StartLED, StartLEDStates
from surrortg import Game


class ArcadePinballGame(Game):
    async def on_init(self):
        # connect pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio")

        # init inputs
        self.left_flipper = ArcadeButton(
            self.pi, LEFT_FLIPPER_PIN, "left", self.abuse_function
        )
        self.right_flipper = ArcadeMultiButton(
            self.pi, RIGHT_FLIPPER_PINS, "right", self.abuse_function
        )
        self.magnet_button = ArcadeButton(
            self.pi, MAGNET_BUTTON_SLAM_TILT_PIN, "magnet", self.abuse_function
        )
        self.start_button = ArcadeButton(self.pi, START_BUTTON_PIN, "start")
        self.service_credit_button = ArcadeButton(
            self.pi, SERVICE_CREDIT_BUTTON_PIN, "service"
        )

        self.plunger = Plunger(self.io, self.pi, PLUNGER_PIN, BALL_SENSOR_PIN)
        self.start_led = StartLED(self.io, self.pi, START_BUTTON_LED_PIN)

        # register inputs
        # TODO each customer might have different amount of buttons!
        self.io.register_inputs(
            {
                "left": self.left_flipper,
                "right": self.right_flipper,
                "magnet": self.magnet_button,
                "plunger": self.plunger,
            }
        )

        # set state flags
        # started_properly must be True first, or might never start
        self.game_started_properly = True
        self.game_ended_properly = False

        # add single credit if not already there
        # this make the start LED flash after game end
        if GAME_MODE == GameModes.PAID:
            await self.add_single_credit_if_none()

    async def on_prepare(self):
        # make sure the previous game has started
        if not self.game_started_properly:
            await self.wait_for_previous_game_start()

        # make sure the previous game has ended
        await self.wait_for_blinking_to_start()

    async def on_start(self):
        await self.start_game()

        self.game_started_properly = False
        await self.wait_for_blinking_to_end()
        self.game_started_properly = True

        await self.wait_for_blinking_to_start()
        await self.end_game()

    async def on_finish(self):
        self.io.disable_inputs()

    async def on_exit(self, reason, exception):
        # shutdown everything
        for input_ in [
            self.left_flipper,
            self.right_flipper,
            self.magnet_button,
            self.plunger,
            self.start_led,
        ]:
            await input_.shutdown()
        # stop pigpio
        self.pi.stop()

    # Abuse callback only resets inputs for arcade if
    # a button is held for too long
    async def abuse_function(self):
        self.io.disable_inputs()
        await self.io.reset_inputs()
        await asyncio.sleep(ABUSE_SLEEP)
        self.io.enable_inputs()

    async def add_single_credit_if_none(self):
        try:
            logging.info("Checking if has credits already")
            await asyncio.wait_for(
                self.wait_for_blinking_to_start(),
                timeout=MAX_BLINKING_START_WAIT_DURING_INIT,
            )
            logging.info("Was already blinking, had credits")
        except asyncio.TimeoutError:
            logging.info("Was not blinking, adding single credit")
            await self.service_credit_button.single_press()

    async def wait_for_previous_game_start(self):
        try:
            logging.info("Previous game did not start properly, waiting...")
            await asyncio.wait_for(
                self.wait_for_blinking_to_end(),
                timeout=MAX_BLINKING_START_WAIT_DURING_PREPARE,
            )
            logging.info("Previous game started")
        except asyncio.TimeoutError:
            logging.warning(
                "Previous game did not start in "
                f"{MAX_BLINKING_START_WAIT_DURING_PREPARE} seconds. "
                "Maybe it actually had started properly. Proceeding."
            )

    async def start_game(self):
        self.game_ended_properly = False
        logging.info("Starting new game on the machine")
        self.plunger.reset_ball_counter()

        # add credit before start if in paid mode
        if GAME_MODE == GameModes.PAID:
            await self.service_credit_button.single_press()
            await asyncio.sleep(1)

        await self.start_button.single_press()

    async def end_game(self):
        self.game_ended_properly = True
        self.io.send_score(score=1, final_score=True)
        logging.info("game ended")

    async def wait_for_blinking_to_end(self):
        logging.info("waiting for the blinking to end")
        while self.start_led.get_state() == StartLEDStates.BLINKING:
            await asyncio.sleep(1)
        logging.info("blinking ended")

    async def wait_for_blinking_to_start(self):
        logging.info("waiting for the blinking to start")
        while self.start_led.get_state() != StartLEDStates.BLINKING:
            await asyncio.sleep(1)
        logging.info("blinking started")


if __name__ == "__main__":
    ArcadePinballGame().run()
