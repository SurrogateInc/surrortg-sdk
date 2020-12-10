import logging
import asyncio
import pigpio
from surrortg import Game
from surrortg.inputs import Directions
from games.claw.claw_joystick import ClawJoystick
from games.claw.claw_button import ClawButton
from games.claw.claw_toy_sensor import ClawToySensor
from games.claw.claw_arduino_toy_sensor import ClawArduinoToySensor
from games.claw.config import (
    ABSOLUTE_GAME_MAX_TIME,
    TOY_WAIT_TIME,
    USE_INTERNAL_IR_SENSOR,
    JOYSTICK_DISABLE_PIN,
    STOP_TIME_BEFORE_BTN_PRESS,
    AUTOMATIC_MOVE_TIME,
    WAIT_TIME_AFTER_SENSOR_BLOCKED,
    BLOCKED_SENSOR_PING_TIME,
    BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED,
)


class ClawGame(Game):
    async def on_init(self):
        # connect to pigpio daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio")

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
            if USE_INTERNAL_IR_SENSOR
            else ClawArduinoToySensor(self.io)
        )

        # init claw machine state variables
        self.ready_for_next_game = False
        self.button_pressed = False

        self.io.register_inputs(
            {"joystick_main": self.joystick, "button_main": self.button,}
        )

    async def on_prepare(self):
        await self.joystick.reset()
        # make sure the prize sensor is not blocked
        if self.toy_sensor.is_blocked():
            if BLOCK_GAME_LOOP_IF_SENSOR_BLOCKED:
                logging.warning(
                    "TOY SENSOR BLOCKED, PLEASE REMOVE BLOCKING OBJECTS"
                )
                # continue game after the blocking objects have been removed
                while True:
                    await asyncio.sleep(BLOCKED_SENSOR_PING_TIME)
                    if not self.toy_sensor.is_blocked():
                        logging.info(
                            f"Toy sensor not stuck anymore, will continue "
                            f"game in {WAIT_TIME_AFTER_SENSOR_BLOCKED} seconds"
                        )
                        await asyncio.sleep(WAIT_TIME_AFTER_SENSOR_BLOCKED)
                        break
            else:
                logging.warning(
                    "TOY SENSOR BLOCKED, BUT PROCEEDING ANYWAY "
                    "(configured not to block game loop while stuck)"
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
            await asyncio.sleep(ABSOLUTE_GAME_MAX_TIME)
            logging.warning(
                "ABSOLUTE_GAME_MAX_TIME passed, this should never happen"
            )
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

        # enable physical joystick
        self.pi.write(JOYSTICK_DISABLE_PIN, 0)

        # set flag that game was played until the end so time consuming
        # preparations are not needed in prepare_game
        self.ready_for_next_game = True

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
        self.pi.stop()


ClawGame().run()
