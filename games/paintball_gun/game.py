import asyncio
import logging

import keyboard

from games.paintball_gun.config import (
    MAX_TRIGGER_PRESSES,
    ON_LEVEL_LOW,
    TRIGGER_PIN,
)
from surrortg import Game
from surrortg.devices import Relay
from surrortg.inputs import Switch


class TriggerSwitch(Switch):
    def __init__(self, pin, max_presses, on_level_low):
        self.relay = Relay(pin, on_level_low)
        self.max_presses = max_presses
        self.press_count = 0

    async def on(self, seat=0):
        # Press only if max press count is not yet reached
        if self.press_count < self.max_presses:
            self.press_count += 1
            self.relay.on()
            logging.info("Trigger pressed")
        else:
            logging.info("Max press count reached")

    async def off(self, seat=0):
        self.relay.off()
        logging.info("Trigger released")

    def reset_press_count(self):
        self.press_count = 0

    async def shutdown(self, seat=0):
        self.relay.stop()


class PaintballGunGame(Game):
    async def on_init(self):
        # Initialize input
        self.trigger = TriggerSwitch(
            TRIGGER_PIN, MAX_TRIGGER_PRESSES, ON_LEVEL_LOW
        )

        # Register input
        self.io.register_inputs({"trigger": self.trigger})

    async def on_prepare(self):
        # Unbind game winner handler from key press event
        self.safe_keyboard_unhook()

    async def on_pre_game(self):
        # Reset trigger press count
        self.trigger.reset_press_count()
        logging.info("Trigger press count reset")

    async def on_start(self):
        logging.info("Game starts")
        # Bind game winner handler to key press event
        self.winner_handler_hook = keyboard.on_press(self.winner_handler)

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()

        try:
            # Wait until the Game Engine ends the game
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            # Unbind game winner handler from key press event
            self.safe_keyboard_unhook()

    async def on_exit(self, reason, exception):
        # Unbind game winner handler from key press event
        self.safe_keyboard_unhook()

    def winner_handler(self, key):
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
        self.safe_keyboard_unhook()

    def safe_keyboard_unhook(self):
        try:
            keyboard.unhook(self.winner_handler_hook)
        except (AttributeError, KeyError):
            pass


if __name__ == "__main__":
    # Start running the game
    PaintballGunGame().run()
