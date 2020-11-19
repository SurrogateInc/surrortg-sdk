import logging
import asyncio
import pigpio
from games.claw.config import (
    IR_SENSOR_PIN,
    TOYSENSOR_STATE_ON,
)


class ClawInternalToySensor:
    def __init__(self, io, pi):
        self.io = io
        self.pi = pi
        self.pi.set_mode(IR_SENSOR_PIN, pigpio.INPUT)

    def get_sensor_state(self):
        sensor_value = self.pi.read(IR_SENSOR_PIN)
        return sensor_value == TOYSENSOR_STATE_ON

    async def wait_for_toy(self, toy_wait_time):
        logging.info("Waiting for toys using internal IR sensor")

        try:
            await asyncio.wait_for(self.detect_toy(), timeout=toy_wait_time)
            toy_amount = 1
        except asyncio.TimeoutError:
            toy_amount = 0

        logging.info(f"Game ended, toy amount was {toy_amount}")
        self.io.send_score(score=toy_amount, final_score=True)

    async def detect_toy(self):
        try:
            if self.get_sensor_state():
                logging.warning(
                    "Toy sensor seems to be blocked! "
                    "No toy result available "
                )
                while True:
                    await asyncio.sleep(1)
            # wait for the toy
            while True:
                if self.get_sensor_state():
                    break
                # give time for wait_for to update
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            raise  # toy detection cancelled
        except Exception as e:
            logging.info(f"Toy detection failed: {e}")

        logging.info(f"Toy found!")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    class DummySocket:
        async def send_score(self, *args, **kwargs):
            pass

    toy_sensor = ClawInternalToySensor(DummySocket())
    asyncio.get_event_loop().run_until_complete(toy_sensor.wait_for_toy(10))
