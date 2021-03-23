import asyncio
import logging

import pigpio

from games.claw.config import (
    BTN_PIN,
    BTN_TIME,
    JOYSTICK_STATE_OFF,
    JOYSTICK_STATE_ON,
)
from surrortg.inputs import Switch


class ClawButton(Switch):
    def __init__(self, pi, pre_press_action=None, post_press_action=None):
        self.pre_press_action = pre_press_action
        self.post_press_action = post_press_action
        self.pi = pi
        self.pi.set_mode(BTN_PIN, pigpio.OUTPUT)
        self.pi.write(BTN_PIN, JOYSTICK_STATE_OFF)

    async def off(self, seat=0):
        pass

    async def on(self, seat=0):
        if self.pre_press_action is not None:
            await self.pre_press_action()
        logging.info("Button pressed")
        self.pi.write(BTN_PIN, JOYSTICK_STATE_ON)
        await asyncio.sleep(BTN_TIME)
        self.pi.write(BTN_PIN, JOYSTICK_STATE_OFF)
        if self.post_press_action is not None:
            await self.post_press_action()

    async def reset(self, seat=0):
        self.pi.write(BTN_PIN, JOYSTICK_STATE_OFF)
