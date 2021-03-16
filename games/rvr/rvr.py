import asyncio
import logging
import os
import sys

from surrortg.inputs import Directions, Joystick

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "./sphero-sdk-raspberrypi-python/"
        )
    )
)
from sphero_sdk import RawMotorModesEnum  # noqa:E402
from sphero_sdk import SerialAsyncDal  # noqa: E402
from sphero_sdk import SpheroRvrAsync  # noqa:E402

# valid speed values are 0-255
# this is used when driving straight or turning on place
SPEED_NORMAL = 150
# these are used when turning while driving
SPEED_FAST = 210
SPEED_SLOW = 50
# stopped speed
SPEED_STOP = 0

# valid motor modes
MODE_FORWARD = RawMotorModesEnum.forward.value
MODE_REVERSE = RawMotorModesEnum.reverse.value
MODE_OFF = RawMotorModesEnum.off.value

# fmt: off
# motor speeds and modes corresponding to the directions
# left_speed, right_speed, left_mode, right_mode
DRIVE_OPTIONS = {
    Directions.MIDDLE:          (SPEED_STOP, SPEED_STOP, MODE_FORWARD, MODE_FORWARD),  # noqa 
    Directions.TOP_RIGHT:       (SPEED_FAST, SPEED_SLOW, MODE_FORWARD, MODE_FORWARD),  # noqa
    Directions.BOTTOM_RIGHT:    (SPEED_FAST, SPEED_SLOW, MODE_REVERSE, MODE_REVERSE),  # noqa
    Directions.BOTTOM_LEFT:     (SPEED_SLOW, SPEED_FAST, MODE_REVERSE, MODE_REVERSE),  # noqa
    Directions.TOP_LEFT:        (SPEED_SLOW, SPEED_FAST, MODE_FORWARD, MODE_FORWARD),  # noqa
    Directions.TOP:             (SPEED_NORMAL, SPEED_NORMAL, MODE_FORWARD, MODE_FORWARD),  # noqa
    Directions.LEFT:            (SPEED_NORMAL, SPEED_NORMAL, MODE_REVERSE, MODE_FORWARD),  # noqa
    Directions.BOTTOM:          (SPEED_NORMAL, SPEED_NORMAL, MODE_REVERSE, MODE_REVERSE),  # noqa
    Directions.RIGHT:           (SPEED_NORMAL, SPEED_NORMAL, MODE_FORWARD, MODE_REVERSE),  # noqa
}
# fmt: on


class RVR(Joystick):
    async def init_sphero(self):
        # init the rvr
        # TODO fix asyncio problems and use the asyncio version
        logging.info("RVR: connecting")
        # serial0 translates either to ttyS0 or ttyAMA0
        self.dal = SerialAsyncDal(
            asyncio.get_running_loop(), port_id="/dev/serial0"
        )
        self.rvr = SpheroRvrAsync(self.dal)

        # fix rvr blocking all default logging after init...
        null_handler = [
            h for h in logging.getLogger().handlers if h.name == "null_handler"
        ][0]
        logging.getLogger().removeHandler(null_handler)

        logging.info("RVR: waking up")
        await self.rvr.wake()
        logging.info("RVR: resetting yaw")
        await self.rvr.reset_yaw()
        logging.info("RVR: init done")

    async def handle_coordinates(self, x, y, seat=0):
        # get direction from the coordinates
        direction = self.get_direction_8(x, y)
        # drive motors based on the direction
        await self.drive(*DRIVE_OPTIONS[direction])

    async def reset(self, seat=0):
        await self.drive(SPEED_STOP, SPEED_STOP, MODE_FORWARD, MODE_FORWARD)

    async def shutdown(self, seat=0):
        # stop the rvr motors
        await self.drive(SPEED_STOP, SPEED_STOP, MODE_OFF, MODE_OFF)
        # close the rvr connection
        await self.rvr.close()

    async def drive(self, left_speed, right_speed, left_mode, right_mode):
        await self.rvr.raw_motors(
            left_speed=left_speed,
            right_speed=right_speed,
            left_mode=left_mode,
            right_mode=right_mode,
        )
