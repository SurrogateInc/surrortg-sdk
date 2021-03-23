import asyncio
import logging

import pigpio

from games.claw.config import (
    SOLENOID_FIRE_INTERVAL,
    SOLENOID_FIRE_PIN,
    SOLENOID_PSU_PIN,
)


class ClawSolenoid:
    def __init__(self, pi):
        self._pi = pi
        self._pi.write(SOLENOID_FIRE_PIN, pigpio.HIGH)
        self._pi.write(SOLENOID_PSU_PIN, pigpio.HIGH)
        self.fire_interval = SOLENOID_FIRE_INTERVAL

    async def fire(self):
        self._pi.write(SOLENOID_FIRE_PIN, pigpio.LOW)
        await asyncio.sleep(0.5)
        self._pi.write(SOLENOID_FIRE_PIN, pigpio.HIGH)
        logging.info("Solenoid fired.")

    async def close(self):
        # Disable solenoid power supply
        self._pi.write(SOLENOID_PSU_PIN, pigpio.LOW)
        # Discharge capacitor
        await self.fire()
