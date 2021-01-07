import asyncio
import logging

import pigpio

from games.claw.config import (
    SOLENOID_FIRE_INTERVAL,
    SOLENOID_PSU_PIN,
    SOLENOID_FIRE_PIN,
)


# time to keep toy reset solenoid in fired state
SOLENOID_FIRE_TIME = 0.5


class ClawSolenoid:
    def __init__(self, pi):
        self._pi = pi
        self._pi.write(SOLENOID_FIRE_PIN, pigpio.HIGH)
        self._pi.write(SOLENOID_PSU_PIN, pigpio.HIGH)
        self.fire_interval = SOLENOID_FIRE_INTERVAL

    async def fire(self):
        self._pi.write(SOLENOID_FIRE_PIN, pigpio.LOW)
        await asyncio.sleep(SOLENOID_FIRE_TIME)
        self._pi.write(SOLENOID_FIRE_PIN, pigpio.HIGH)
        logging.info("Solenoid fired.")

    async def close(self):
        self._pi.write(SOLENOID_PSU_PIN, pigpio.LOW)
        # discharge capacitor
        await self.fire()
