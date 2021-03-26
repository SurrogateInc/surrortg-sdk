import asyncio
import logging

import pigpio

from games.ninswitch.config import TRINKET_RESET_PIN
from surrortg.inputs import Switch


class TrinketResetSwitch(Switch):
    def __init__(self, pi):
        self._pi = pi
        self.reset_lock = asyncio.Lock()

        # Set reset pin to output mode
        self._pi.set_mode(TRINKET_RESET_PIN, pigpio.OUTPUT)
        # Trinket reset pin is active LOW, set out of reset
        self._pi.write(TRINKET_RESET_PIN, pigpio.HIGH)

    async def reset_trinket(self):
        # Skip reset if it is already in progress
        if self.reset_lock.locked():
            return

        async with self.reset_lock:
            logging.info("Trinket reset.")
            self._pi.write(TRINKET_RESET_PIN, pigpio.LOW)
            await asyncio.sleep(0.1)
            self._pi.write(TRINKET_RESET_PIN, pigpio.HIGH)
            # Wait until Trinket wakes up from reset
            await asyncio.sleep(3)

    async def on(self, seat=0):
        await self.reset_trinket()

    async def off(self, seat=0):
        pass

    def close(self):
        self._pi.set_mode(TRINKET_RESET_PIN, pigpio.INPUT)
