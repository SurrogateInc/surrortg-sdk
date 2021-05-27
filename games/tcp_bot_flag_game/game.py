import asyncio
import logging

import keyboard

from games.tcp_bot_flag_game.config import (
    SERVO_MAX_PULSE_WIDTH,
    SERVO_MIN_FULL_SWEEP_TIME,
    SERVO_MIN_PULSE_WIDTH,
    SERVO_PIN,
    SERVO_ROTATION_UPDATE_FREQ,
    SERVO_WAIT_BETWEEN_MOVE,
)
from surrortg import Game
from surrortg.devices import Servo
from surrortg.devices.tcp import TcpCar


class TcpBotFlagGame(Game):
    async def on_init(self):
        # Create the TCP bot
        # TcpCar can be used as it has the correct controls (throttle and
        # steering) configured as a joystick
        self.bot = TcpCar(self.io)

        # Register inputs
        self.io.register_inputs(self.bot.inputs)

        self.wrecking_ball_task = None
        self.wrecking_ball_servo = Servo(
            SERVO_PIN,
            SERVO_MIN_PULSE_WIDTH,
            SERVO_MAX_PULSE_WIDTH,
            SERVO_MIN_FULL_SWEEP_TIME,
            SERVO_ROTATION_UPDATE_FREQ,
        )
        await self.wrecking_ball_servo.rotate_to(0)

    async def on_config(self):
        self.wrecking_ball_enabled(False)
        set_num = await self.bot.handle_config(self.configs)
        # Unbind game winner handler from key press event
        self.safe_keyboard_unhook()
        return set_num

    async def on_start(self):
        self.winner_handler_hook = keyboard.on_press(
            self.keyboard_winner_handler
        )
        self.wrecking_ball_enabled(True)

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()
        self.wrecking_ball_enabled(False)

        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            # Unbind game winner handler from key press event
            self.safe_keyboard_unhook()

    def send_score(self, scores):
        logging.info(f"Ending game with scores: {scores}")
        self.io.send_score(scores=scores, final_score=True)

    def safe_keyboard_unhook(self):
        try:
            keyboard.unhook(self.winner_handler_hook)
        except (AttributeError, KeyError):
            pass

    def keyboard_winner_handler(self, key):
        if key.name == "1":
            logging.info("Win for bot 1")
            self.send_score([1, 0])
        elif key.name == "2":
            logging.info("Win for bot 2")
            self.send_score([0, 1])
        elif key.name == "0":
            logging.info("Draw")
            self.send_score([0, 0])
        else:
            logging.info(
                "Wrong key pressed. Press '1' for bot 1 win,"
                "'2' for bot 2 win and '0' for draw"
            )
            return

        self.safe_keyboard_unhook()

    def wrecking_ball_enabled(self, enable):
        if self.wrecking_ball_task is not None:
            self.wrecking_ball_task.cancel()

        if enable:
            self.wrecking_ball_task = asyncio.create_task(
                self.repeat_wrecking_ball_movement()
            )

    async def repeat_wrecking_ball_movement(self):
        while True:
            await self.wrecking_ball_servo.rotate_to(-1)
            await asyncio.sleep(SERVO_WAIT_BETWEEN_MOVE)
            await self.wrecking_ball_servo.rotate_to(1)
            await asyncio.sleep(SERVO_WAIT_BETWEEN_MOVE)


if __name__ == "__main__":
    TcpBotFlagGame().run()
