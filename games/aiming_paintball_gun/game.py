import asyncio
import logging

import keyboard

from games.aiming_paintball_gun.config import (
    MAX_TRIGGER_PRESSES,
    ON_LEVEL_LOW,
    SERVO_MAX_PULSE_WIDTH,
    SERVO_MIN_FULL_SWEEP_TIME,
    SERVO_MIN_PULSE_WIDTH,
    SERVO_PIN,
    SERVO_ROTATION_UPDATE_FREQ,
    TRIGGER_PIN,
)
from surrortg import Game
from surrortg.devices import Relay, Servo
from surrortg.inputs import Joystick, Switch


class ServoJoystick(Joystick):
    def __init__(self, servo):
        self.servo = servo
        self.is_on = False

    async def handle_coordinates(self, x, y, seat=0):
        if self.is_on:
            self.servo.rotation_speed = x

    async def enable(self):
        self.is_on = True

    async def disable(self):
        await self.handle_coordinates(0, 0)
        self.is_on = False


class TriggerSwitch(Switch):
    def __init__(self, pin, max_presses, max_press_cb, on_level_low):
        self.relay = Relay(pin, on_level_low)
        self.max_presses = max_presses
        self.press_count = 0
        self.max_press_cb = max_press_cb

    async def on(self, seat=0):
        # Press only if max press count is not yet reached
        if self.press_count < self.max_presses:
            self.press_count += 1
            self.relay.on()
            logging.info("Trigger pressed")
            if self.press_count == self.max_presses:
                await self.max_press_cb()
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
        # Initialize inputs
        self.trigger = TriggerSwitch(
            TRIGGER_PIN,
            MAX_TRIGGER_PRESSES,
            self.max_presses_handler,
            ON_LEVEL_LOW,
        )
        self.servo = Servo(
            SERVO_PIN,
            SERVO_MIN_PULSE_WIDTH,
            SERVO_MAX_PULSE_WIDTH,
            SERVO_MIN_FULL_SWEEP_TIME,
            SERVO_ROTATION_UPDATE_FREQ,
        )
        self.servo_joystick = ServoJoystick(self.servo)

        # Register inputs
        self.io.register_inputs(
            {
                "trigger": self.trigger,
                "aim": self.servo_joystick,
            }
        )

    def safe_keyboard_unhook(self):
        try:
            keyboard.unhook(self.winner_handler_hook)
        except (AttributeError, KeyError):
            pass

    async def on_config(self):
        # Unbind game winner handler from key press event
        self.safe_keyboard_unhook()

    async def on_pre_game(self):
        # Reset trigger press count
        self.trigger.reset_press_count()
        await self.servo.rotate_to(0)
        await self.servo_joystick.enable()
        logging.info("Trigger press count and servo reset")

    async def on_start(self):
        logging.info("Game starts")
        # Bind game winner handler to key press event
        self.winner_handler_hook = keyboard.on_press(self.winner_handler)

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()

        try:
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

    async def max_presses_handler(self):
        await self.servo_joystick.disable()


if __name__ == "__main__":
    # Start running the game
    PaintballGunGame().run()
