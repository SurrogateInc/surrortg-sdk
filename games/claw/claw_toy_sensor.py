import asyncio
import logging

import pigpio

from games.claw.config import TOY_SENSOR_PIN, TOY_SENSOR_STATE_BLOCKED


class ClawToySensor:
    def __init__(self, pi):
        self.pi = pi
        self.pi.set_mode(TOY_SENSOR_PIN, pigpio.INPUT)

    def is_blocked(self):
        return self.pi.read(TOY_SENSOR_PIN) == TOY_SENSOR_STATE_BLOCKED

    async def toy_detected(self, toy_wait_time):
        """Wait until toy is detected or timeout is reached.

        :param toy_wait_time: Timeout in seconds if toy is not detected.
        :type toy_wait_time: int or float
        :return: If toy was detected or not
        :rtype: bool
        """
        logging.info("Waiting for toy")
        try:
            await asyncio.wait_for(self._wait_for_toy(), timeout=toy_wait_time)
            logging.info("Toy detected")
            return True
        except asyncio.TimeoutError:
            logging.info("No toy detected")
            return False

    async def _wait_for_toy(self):
        try:
            while True:
                # Toy found if sensor is blocked
                if self.is_blocked():
                    break
                # Give wait_for() time to update
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    # Connect to pigpio daemon
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("Could not connect to pigpio daemon")

    toy_sensor = ClawToySensor(pi)
    asyncio.get_event_loop().run_until_complete(toy_sensor.toy_detected(10))
