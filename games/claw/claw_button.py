import logging
import asyncio
import pigpio
from surrortg.inputs import Switch
from games.claw.config import BTN_PIN, BTN_TIME


class ClawButton(Switch):
    def __init__(self, pi, pre_press_action=None, post_press_action=None):
        self.pre_press_action = pre_press_action
        self.post_press_action = post_press_action
        self.pi = pi
        self.pi.set_mode(BTN_PIN, pigpio.OUTPUT)
        self.pi.write(BTN_PIN, 1)

    async def off(self, seat=0):
        pass

    async def on(self, seat=0):
        if self.pre_press_action is not None:
            await self.pre_press_action()
        logging.info(f"Button pressed")
        self.pi.write(BTN_PIN, 0)
        await asyncio.sleep(BTN_TIME)
        self.pi.write(BTN_PIN, 1)
        if self.post_press_action is not None:
            await self.post_press_action()

    async def reset(self, seat=0):
        self.pi.write(BTN_PIN, 1)
