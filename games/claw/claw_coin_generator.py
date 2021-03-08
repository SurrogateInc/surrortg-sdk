import asyncio

import pigpio

from games.claw.config import COIN_SIGNAL_PIN


class ClawCoinGenerator:
    def __init__(self, pi):
        self._pi = pi
        self._pi.set_mode(COIN_SIGNAL_PIN, pigpio.OUTPUT)
        self._pi.write(COIN_SIGNAL_PIN, pigpio.LOW)

    async def insert_coin(self):
        self._pi.write(COIN_SIGNAL_PIN, pigpio.HIGH)
        await asyncio.sleep(0.5)
        self._pi.write(COIN_SIGNAL_PIN, pigpio.LOW)
        await asyncio.sleep(0.5)

    def close(self):
        self._pi.set_mode(COIN_SIGNAL_PIN, pigpio.INPUT)
