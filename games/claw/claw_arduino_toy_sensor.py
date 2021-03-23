import asyncio
import logging

import serial

from games.claw.config import ARDUINO_PATH, BLOCKED_THRESHOLD


class ClawArduinoToySensor:
    def __init__(self, io):
        self.io = io

    def is_blocked(self):
        """This function only exists for compatibility reasons."""
        return 0

    async def wait_for_toy(self, toy_wait_time):
        logging.info("Waiting for toys")

        try:
            await asyncio.wait_for(self.detect_toy(), timeout=toy_wait_time)
            toy_amount = 1
        except asyncio.TimeoutError:
            toy_amount = 0

        logging.info(f"Game ended, toy amount was {toy_amount}")
        self.io.send_score(score=toy_amount, final_score=True)

    async def detect_toy(self):
        try:
            with serial.Serial(ARDUINO_PATH) as ser:
                # Log the smallest sensor setup value
                ser.timeout = 2
                try:
                    smallest_measurement = int(self._get_line(ser))
                    logging.info(
                        f"Smallest setup measurement: {smallest_measurement}"
                    )
                    if smallest_measurement < BLOCKED_THRESHOLD:
                        logging.warning(
                            "Toy sensor seems to be blocked! "
                            "No toy result available"
                        )
                        while True:
                            await asyncio.sleep(1)
                except asyncio.CancelledError:
                    raise  # Toy detection cancelled
                except Exception as e:
                    logging.info(
                        f"smallest_measurement parsing failed: {e}, "
                        "maybe just missed first line or timeouted"
                    )

                # Wait for the toy
                ser.timeout = 0.1
                while True:
                    if self._get_line(ser) == "D":
                        break
                    # Give time for wait_for to update
                    await asyncio.sleep(0.1)

        except serial.SerialException as e:
            logging.warning(
                f"Serial connection failed: {e},\n\nNo toy result available"
            )
            while True:
                await asyncio.sleep(1)

        logging.info("Toy found!")

    @staticmethod
    def _get_line(ser):
        # read_until does only block for ser.timeout unlike ser.readline
        return ser.read_until(b"\n").decode("ascii", errors="ignore").rstrip()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    class DummySocket:
        async def send(self, *args):
            pass

    toy_sensor = ClawArduinoToySensor(DummySocket())
    asyncio.get_event_loop().run_until_complete(toy_sensor.wait_for_toy(5))
