import logging
import asyncio

import pigpio

from surrortg import Game
from surrortg.inputs import Directions
from games.claw.claw_joystick import ClawJoystick
from games.claw.claw_button import ClawButton
from games.claw.claw_toy_sensor import ClawToySensor
from games.claw.claw_arduino_toy_sensor import ClawArduinoToySensor
from games.claw.claw_toy_reset_solenoid import ClawSolenoid
from games.claw.config import (
    USE_INTERNAL_TOY_SENSOR,
    USE_JOYSTICK_SPLITTER,
    USE_TOY_RESET_SOLENOID,
    USE_COIN_SIGNAL_GENERATOR,
    BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED,
    BLOCKED_SENSOR_PING_INTERVAL,
    WAIT_TIME_AFTER_SENSOR_CLEARED,
    TOY_WAIT_TIME,
    CLAW_PICK_CYCLE_TIME,
    CLAW_CORNER_TO_CORNER_TIME,
    CLAW_GAME_LENGTH,
    STOP_TIME_BEFORE_BTN_PRESS,
    AUTOMATIC_MOVE_TIME,
    JOYSTICK_DISABLE_PIN,
    COIN_SIGNAL_PIN,
    GE_GAME_LENGTH,
)


class ClawGame(Game):
    async def on_init(self):
        # connect to pigpio daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio")

        if USE_JOYSTICK_SPLITTER:
            # init joystick splitter, enable physical joystick by default
            self.pi.set_mode(JOYSTICK_DISABLE_PIN, pigpio.OUTPUT)
            self.pi.write(JOYSTICK_DISABLE_PIN, 0)

        # init claw machine parts
        self.joystick = ClawJoystick(self.pi)
        self.button = ClawButton(
            pi=self.pi,
            pre_press_action=self.pre_button_press,
            post_press_action=self.post_button_press,
        )
        self.toy_sensor = (
            ClawToySensor(io=self.io, pi=self.pi)
            if USE_INTERNAL_TOY_SENSOR
            else ClawArduinoToySensor(self.io)
        )

        if USE_TOY_RESET_SOLENOID:
            # init toy reset solenoid
            self.solenoid = ClawSolenoid(self.pi)

        if USE_COIN_SIGNAL_GENERATOR:
            self.pi.set_mode(COIN_SIGNAL_PIN, pigpio.OUTPUT)
            self.coin_signal_generator_task = asyncio.create_task(
                self._coin_signal_generator()
            )

        # init claw machine state variables
        self.ready_for_next_game = False
        self.button_pressed = False

        self.io.register_inputs(
            {"joystick_main": self.joystick, "button_main": self.button,}
        )

    async def on_prepare(self):
        await self.joystick.reset()

        if self.toy_sensor.is_blocked():
            if USE_TOY_RESET_SOLENOID:
                await self.solenoid_toy_reset_loop()
            elif BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED:
                logging.warning(
                    "TOY SENSOR BLOCKED, PLEASE REMOVE BLOCKING OBJECTS"
                )
                # wait until blocking objects have been removed
                while True:
                    await asyncio.sleep(BLOCKED_SENSOR_PING_INTERVAL)
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

        # make sure the state is correct before approving game start
        if not self.ready_for_next_game:
            logging.info("Forcing the ClawMachine ready state, please wait...")
            await self.enable_button()
            await self.button.on()
            await asyncio.sleep(TOY_WAIT_TIME)
            self.ready_for_next_game = True
            logging.info("...ClawMachine ready")

    async def on_pre_game(self):
        if USE_JOYSTICK_SPLITTER:
            # disable the physical joystick
            self.pi.write(JOYSTICK_DISABLE_PIN, 1)

        await self.enable_button()
        self.io.send_pre_game_ready()

    async def on_start(self):
        await self.joystick.reset()
        logging.info("Playing started")

        # set a flag for checking that the game has been finished
        # will be set back to True only if finish_game gets to the end
        self.ready_for_next_game = False

        # this flag makes sure that the button will always be pressed
        # by the player or the GE
        self.button_pressed = False

        # play game until player pushes button or time is up and GE moves to
        # on finish. This game section should never finish by itself
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

        # push the button if not done by the user
        if not self.button_pressed:
            await self.button.on()

        # wait for toy and send result
        await self.toy_sensor.wait_for_toy(TOY_WAIT_TIME)

        if USE_JOYSTICK_SPLITTER:
            # enable physical joystick
            self.pi.write(JOYSTICK_DISABLE_PIN, 0)

        # set flag that game was played until the end so time consuming
        # preparations are not needed in prepare_game
        self.ready_for_next_game = True

    async def solenoid_toy_reset_loop(self):
        reset_task_timeout = (
            CLAW_GAME_LENGTH - 2 * CLAW_CORNER_TO_CORNER_TIME - 10
        )
        while True:
            try:
                # run solenoid reset task until it succeeds or timeouts
                logging.info("Solenoid toy reset task started.")
                await asyncio.wait_for(
                    self._solenoid_toy_reset_task(), timeout=reset_task_timeout
                )
                logging.info("Solenoid toy reset task completed.")
                break
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logging.info("Solenoid reset task timeouted. Starting again.")
                # move claw back to bottom left corner
                self.joystick.move(Directions.BOTTOM_LEFT)
                await asyncio.sleep(CLAW_CORNER_TO_CORNER_TIME)
                await self.joystick.reset()

                # pick with claw to end game
                await self.button.on(seat=0)
                # wait until claw has completed picking cycle
                await asyncio.sleep(CLAW_PICK_CYCLE_TIME)

    async def _solenoid_toy_reset_task(self):
        # move claw to top right corner
        self.joystick.move(Directions.TOP_RIGHT)
        await asyncio.sleep(CLAW_CORNER_TO_CORNER_TIME)
        await self.joystick.reset()

        while True:
            # fire toy reset solenoid
            await asyncio.shield(self.solenoid.fire())
            await asyncio.sleep(self.solenoid.fire_interval)

            # if toy reset succeeded
            if not self.toy_sensor.is_blocked():
                # move claw back to bottom left
                self.joystick.move(Directions.BOTTOM_LEFT)
                await asyncio.sleep(CLAW_CORNER_TO_CORNER_TIME)
                await self.joystick.reset()

                # pick with claw to end game
                await self.button.on(seat=0)
                # wait until claw has completed picking cycle
                await asyncio.sleep(CLAW_PICK_CYCLE_TIME)
                break

            # if toy reset failed
            else:
                logging.info("Toy reset failed, trying again.")

    async def enable_button(self):
        # move and stop to start game in the machine timer, because the
        # drop claw button can't be used before moving.
        # 'ur' + 'dl' forces the claw to move regardless of the current
        # position
        for direction in [
            Directions.TOP_RIGHT,
            Directions.MIDDLE,
            Directions.BOTTOM_LEFT,
            Directions.MIDDLE,
        ]:
            self.joystick.move(direction)
            await asyncio.sleep(AUTOMATIC_MOVE_TIME)

    async def pre_button_press(self):
        self.io.disable_inputs()
        await self.joystick.reset()
        await asyncio.sleep(STOP_TIME_BEFORE_BTN_PRESS)

    async def post_button_press(self):
        self.button_pressed = True
        logging.info("sending playingEnded")
        self.io.send_playing_ended()

    async def on_exit(self, reason, exception):
        if USE_TOY_RESET_SOLENOID:
            await self.solenoid.close()
        self.pi.stop()

    async def _coin_signal_generator(self):
        while True:
            self.pi.write(COIN_SIGNAL_PIN, pigpio.HIGH)
            await asyncio.sleep(0.5)
            self.pi.write(COIN_SIGNAL_PIN, pigpio.LOW)
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    ClawGame().run()
