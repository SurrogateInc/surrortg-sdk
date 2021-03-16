import asyncio
import logging

import pigpio

from games.claw.claw_button import ClawButton
from games.claw.claw_coin_generator import ClawCoinGenerator
from games.claw.claw_joystick import ClawJoystick
from games.claw.claw_joystick_splitter import ClawJoystickSplitter
from games.claw.claw_toy_reset_solenoid import ClawSolenoid
from games.claw.claw_toy_sensor import ClawToySensor
from games.claw.config import (
    AUTOMATIC_MOVE_TIME,
    BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED,
    CLAW_CORNER_TO_CORNER_TIME,
    CLAW_GAME_LENGTH,
    CLAW_PICK_CYCLE_TIME,
    GE_GAME_LENGTH,
    STOP_TIME_BEFORE_BTN_PRESS,
    TOY_WAIT_TIME,
    USE_COIN_GENERATOR,
    USE_JOYSTICK_SPLITTER,
    USE_TOY_RESET_SOLENOID,
    WAIT_TIME_AFTER_SENSOR_CLEARED,
)
from surrortg import Game
from surrortg.inputs import Directions


class ClawGame(Game):
    async def on_init(self):
        # Connect to pigpio daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")

        # Initialize claw machine parts
        self.joystick = ClawJoystick(self.pi)
        self.button = ClawButton(
            pi=self.pi,
            pre_press_action=self._pre_button_press,
            post_press_action=self._post_button_press,
        )
        self.toy_sensor = ClawToySensor(self.pi)

        # Initialize optional claw machine parts
        if USE_COIN_GENERATOR:
            self.coin_generator = ClawCoinGenerator(self.pi)
        if USE_TOY_RESET_SOLENOID:
            self.solenoid = ClawSolenoid(self.pi)
        if USE_JOYSTICK_SPLITTER:
            self.joystick_splitter = ClawJoystickSplitter(self.pi)

        # Initialize claw machine state variables
        self.ready_for_next_game = False
        self.button_pressed = False
        # Assume that previous game was a win in case software crashes.
        # Causes toy reset cycle during software startup if toy reset
        # solenoid system is enabled.
        self.previous_game_won = True

        # Register claw machine inputs
        self.io.register_inputs(
            {
                "joystick_main": self.joystick,
                "button_main": self.button,
            }
        )

    async def on_prepare(self):
        await self.joystick.reset()

        if USE_TOY_RESET_SOLENOID and (
            self.toy_sensor.is_blocked() or self.previous_game_won
        ):
            self.previous_game_won = False
            await self._solenoid_toy_reset_loop()
        elif self.toy_sensor.is_blocked():
            if BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED:
                logging.warning(
                    "TOY SENSOR BLOCKED, PLEASE REMOVE BLOCKING OBJECTS"
                )
                # Wait until blocking objects have been removed
                while True:
                    await asyncio.sleep(1)
                    if not self.toy_sensor.is_blocked():
                        logging.info(
                            f"Toy sensor not blocked anymore, will continue "
                            f"game in {WAIT_TIME_AFTER_SENSOR_CLEARED} seconds"
                        )
                        await asyncio.sleep(WAIT_TIME_AFTER_SENSOR_CLEARED)
                        break
            else:
                logging.warning(
                    "TOY SENSOR BLOCKED, BUT PROCEEDING ANYWAY "
                    "(configured not to block game loop if sensor is blocked)"
                )

        # Make sure the state is correct before approving game start
        if not self.ready_for_next_game:
            logging.info("Forcing the ClawMachine ready state, please wait...")
            await self.start_claw_game()
            await self.button.on()
            await asyncio.sleep(TOY_WAIT_TIME)
            self.ready_for_next_game = True
            logging.info("...ClawMachine ready")

    async def on_pre_game(self):
        if USE_JOYSTICK_SPLITTER:
            # Disable physical joystick
            self.joystick_splitter.disable_joystick()

        await self.start_claw_game()
        self.io.send_pre_game_ready()

    async def on_start(self):
        await self.joystick.reset()
        logging.info("Playing started")

        # Set a flag for checking that the game has been finished.
        # Will be set back to True only if finish_game gets to the end.
        self.ready_for_next_game = False

        # This flag makes sure that the button will always be pressed
        # by the player or the GE.
        self.button_pressed = False

        # Play game until player pushes button or time is up and GE moves to
        # on_finish(). This game section should never finish by itself.
        try:
            await asyncio.sleep(GE_GAME_LENGTH + 10)
            logging.warning("GE_GAME_LENGTH passed, this should never happen")
            self.io.disable_inputs()
            await self.joystick.reset()
            self.io.send_playing_ended()
        except asyncio.CancelledError:
            logging.info("GE ended playing")

    async def on_finish(self):
        await self.joystick.reset()

        # Push the button if not done by the user
        if not self.button_pressed:
            await self.button.on()

        # Wait for the toy and send result
        game_won = await self.toy_sensor.toy_detected(TOY_WAIT_TIME)
        score = 1 if game_won else 0
        self.io.send_score(score=score, final_score=True)
        self.previous_game_won = game_won

        if USE_JOYSTICK_SPLITTER:
            # Enable physical joystick
            self.joystick_splitter.enable_joystick()

        # Set flag that game was played until the end so time consuming
        # preparations are not needed in on_prepare().
        self.ready_for_next_game = True

    async def on_exit(self, reason, exception):
        if USE_COIN_GENERATOR:
            self.coin_generator.close()
        if USE_TOY_RESET_SOLENOID:
            await self.solenoid.close()
        if USE_JOYSTICK_SPLITTER:
            self.joystick_splitter.close()
        self.pi.stop()

    async def start_claw_game(self):
        if USE_COIN_GENERATOR:
            await self.coin_generator.insert_coin()

        # Move claw to start claw machine internal game timer (claw button
        # can't be used before activating game timer). 'ur' + 'dl' forces the
        # claw to move regardless of the current position.
        for direction in [
            Directions.TOP_RIGHT,
            Directions.MIDDLE,
            Directions.BOTTOM_LEFT,
            Directions.MIDDLE,
        ]:
            self.joystick.move(direction)
            await asyncio.sleep(AUTOMATIC_MOVE_TIME)

    async def _pre_button_press(self):
        self.io.disable_inputs()
        await self.joystick.reset()
        await asyncio.sleep(STOP_TIME_BEFORE_BTN_PRESS)

    async def _post_button_press(self):
        self.button_pressed = True
        logging.info("sending playingEnded")
        self.io.send_playing_ended()

    async def _solenoid_toy_reset_loop(self):
        reset_task_timeout = (
            CLAW_GAME_LENGTH - 2 * CLAW_CORNER_TO_CORNER_TIME - 10
        )
        while True:
            try:
                # Run solenoid reset task until it succeeds or timeouts
                logging.info("Solenoid toy reset task started.")
                await asyncio.wait_for(
                    self._solenoid_toy_reset_task(), timeout=reset_task_timeout
                )
                logging.info("Solenoid toy reset task completed.")
                break
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logging.info("Solenoid reset task timeouted. Starting again.")
                # Move claw back to bottom left corner
                self.joystick.move(Directions.BOTTOM_LEFT)
                await asyncio.sleep(CLAW_CORNER_TO_CORNER_TIME)
                await self.joystick.reset()

                # Pick with claw to end game
                await self.button.on()
                await asyncio.sleep(CLAW_PICK_CYCLE_TIME)

    async def _solenoid_toy_reset_task(self):
        # Move claw to top right corner
        await self.start_claw_game()
        self.joystick.move(Directions.TOP_RIGHT)
        await asyncio.sleep(CLAW_CORNER_TO_CORNER_TIME)
        await self.joystick.reset()

        while True:
            # Fire toy reset solenoid
            await asyncio.shield(self.solenoid.fire())
            await asyncio.sleep(self.solenoid.fire_interval)

            # If toy reset succeeded
            if not self.toy_sensor.is_blocked():
                # Move claw back to bottom left
                self.joystick.move(Directions.BOTTOM_LEFT)
                await asyncio.sleep(CLAW_CORNER_TO_CORNER_TIME)
                await self.joystick.reset()

                # Pick with claw to end game
                await self.button.on(seat=0)
                await asyncio.sleep(CLAW_PICK_CYCLE_TIME)
                break

            # If toy reset failed
            else:
                logging.info("Toy reset failed, trying again.")


if __name__ == "__main__":
    ClawGame().run()
