import asyncio

from .udp_actuator import UdpActuator
from .udp_bot import UdpBot


class UdpCar(UdpBot):
    """Class for car-like udp-controlled bots

    Default inputs include throttle and steering,
    defined as two separate actuators

    :param throttle_mult: multiplier for throttle value, defaults to 1.0
    :type throttle_mult: float, optional
    :param steering_mult: multiplier for steering value, defaults to 1.0
    :type steering_mult: float, optional
    :param repeat_commands: defines if commands should be repeated,
        defaults to False
    :type repeat_commands: bool, optional
    """

    def __init__(
        self,
        throttle_mult=1.0,
        steering_mult=1.0,
        repeat_commands=False,
    ):
        super().__init__()
        self._throttle = UdpActuator(0x01, throttle_mult, repeat_commands)
        self._steering = UdpActuator(0x02, steering_mult, repeat_commands)
        self.add_input({"motor": self._throttle})
        self.add_input({"steering": self._steering})

    def threadsafe_throttle(self, val, seat):
        """Threadsafe helper method for using throttle

        Can be used to access the UdpCar's throttle actuator
        :param val: Actuator position value, between -1.0 and 1.0
        :type val: float
        :param seat: Robot seat
        :type seat: int
        """
        asyncio.run_coroutine_threadsafe(
            self._throttle.drive_actuator(val, seat, unscaled=True), self._loop
        )

    def threadsafe_steer(self, val, seat):
        """Threadsafe helper method for using steering

        Can be used to access the UdpCar's steering actuator
        :param val: Actuator position value, between -1.0 and 1.0
        :type val: float
        :param seat: Robot seat
        :type seat: int
        """
        asyncio.run_coroutine_threadsafe(
            self._steering.drive_actuator(val, seat, unscaled=True), self._loop
        )
