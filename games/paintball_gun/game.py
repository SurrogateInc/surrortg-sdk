import asyncio
import logging

import keyboard
import pigpio

from games.paintball_gun.config import (
    MAX_GAME_TIME,
    MAX_TRIGGER_PRESSES,
    ON_LEVEL,
    TRIGGER_PIN,
    WAIT_CONTINUE_DASHBOARD,
    WAIT_CONTINUE_KEYBOARD,
)
from surrortg import Game
from surrortg.inputs import Switch


class TriggerSwitch(Switch):
    def __init__(self, pi, pin, max_presses):
        self._pi = pi
        self.pin = pin
        self.max_presses = max_presses
        self.press_count = 0

        # Set GPIO pin levels according to the configuration
        if ON_LEVEL == "HIGH":
            self.on_level = pigpio.HIGH
            self.off_level = pigpio.LOW
        else:
            self.on_level = pigpio.LOW
            self.off_level = pigpio.HIGH

        # Initialize output pin
        self._pi.set_mode(self.pin, pigpio.OUTPUT)
        self._pi.write(self.pin, self.off_level)

    async def on(self, seat=0):
        # Press only if max press count is not yet reached
        if self.press_count < self.max_presses:
            self.press_count += 1
            self._pi.write(self.pin, self.on_level)
            logging.info("Trigger pressed")
        else:
            logging.info("Max press count reached")

    async def off(self, seat=0):
        self._pi.write(self.pin, self.off_level)
        logging.info("Trigger released")

    def reset_press_count(self):
        self.press_count = 0

    async def shutdown(self, seat=0):
        # Set pin to input mode to make it safe
        self._pi.set_pull_up_down(self.pin, pigpio.PUD_OFF)
        self._pi.set_mode(self.pin, pigpio.INPUT)


class PaintballGunGame(Game):
    async def on_init(self):
        # Connect to pigpio daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")

        self.game_ready = None

        # Initialize input
        self.trigger = TriggerSwitch(self.pi, TRIGGER_PIN, MAX_TRIGGER_PRESSES)

        # Register input
        self.io.register_inputs({"trigger": self.trigger})

    async def on_config(self):
        # Unbind game winner handler from key press event
        try:
            keyboard.unhook(self._winner_handler_hook)
        except (AttributeError, KeyError):
            pass

    async def on_prepare(self):
        # Wait for approval to continue if necessary
        if WAIT_CONTINUE_DASHBOARD:
            logging.info("Press play button to continue to the next game")
            return False
        elif WAIT_CONTINUE_KEYBOARD:
            # Bind game ready handler to key press event
            self._ready_handler_hook = keyboard.on_press_key(
                "enter", self._game_ready_handler
            )

            # Wait until enter is pressed to continue to the next game
            logging.info("Press 'Enter' to continue to the next game")
            self.game_ready = False
            while not self.game_ready:
                await asyncio.sleep(0)

    async def on_pre_game(self):
        # Reset trigger press count
        self.trigger.reset_press_count()
        logging.info("Trigger press count reset")

    async def on_start(self):
        logging.info("Game starts")
        # Bind game winner handler to key press event
        self._winner_handler_hook = keyboard.on_press(self._winner_handler)

        # Play the game until score is manually selected or the time is up
        try:
            await asyncio.sleep(MAX_GAME_TIME)
            logging.warning("MAX_GAME_TIME passed, ending game")
            self.io.disable_inputs()
            self.io.send_score(score=0, final_score=True)
        except asyncio.CancelledError:
            logging.info("GE ended playing")

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()

        # Unbind game winner handler from key press event
        try:
            keyboard.unhook(self._winner_handler_hook)
        except (AttributeError, KeyError):
            pass

    async def on_exit(self, reason, exception):
        # Unbind game winner handler from key press event
        try:
            keyboard.unhook(self._winner_handler_hook)
        except (AttributeError, KeyError):
            pass

        # Unbind game ready handler from key press event
        try:
            keyboard.unhook(self._ready_handler_hook)
        except (AttributeError, KeyError):
            pass

    def _winner_handler(self, key):
        if key.name == "1":
            score = 1
            logging.info("Win selected")
        elif key.name == "0":
            score = 0
            logging.info("Loss selected")
        else:
            logging.info("Wrong key pressed. Press '1' for win, '0' for loss")
            return

        self.io.send_score(score=score, final_score=True)
        keyboard.unhook(self._winner_handler_hook)

    def _game_ready_handler(self, key):
        self.game_ready = True
        keyboard.unhook(self._ready_handler_hook)


if __name__ == "__main__":
    # Start running the game
    PaintballGunGame().run()
