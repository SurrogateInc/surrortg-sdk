import asyncio

from .tcp_bot import TcpBot
from .tcp_joystick import TcpJoystick
from .tcp_protocol import TcpCommandId


class TcpCar(TcpBot):
    """Class for car-like TCP-controlled bots

    Default inputs include throttle and steering,
    defined as two separate actuators

    :param game_io: The game's GameIO object
    :type game_io: GameIO
    :param throttle_mult: multiplier for throttle value, defaults to 1.0
    :type throttle_mult: float, optional
    :param steering_mult: multiplier for steering value, defaults to 1.0
    :type steering_mult: float, optional
    """

    def __init__(
        self,
        game_io,
        throttle_mult=1.0,
        steering_mult=1.0,
    ):
        super().__init__(game_io)
        self._joystick = TcpJoystick(
            TcpCommandId.STEER,
            TcpCommandId.THROTTLE,
            steering_mult,
            throttle_mult,
        )
        self.add_inputs({"drive_joystick": self._joystick})

    def threadsafe_drive(self, throttle, steering, seat):
        """Threadsafe helper method for using both throttle and steering

        :param throttle: Throttle value, between -1.0 and 1.0
        :type throttle: float
        :param steering: Steering value, between -1.0 and 1.0
        :type steering: float
        :param seat: Robot seat
        :type seat: int
        """
        asyncio.run_coroutine_threadsafe(
            self._joystick.handle_coordinates(steering, throttle, seat),
            self._loop,
        )

    def threadsafe_throttle(self, throttle, seat):
        """Threadsafe helper method for using throttle

        :param throttle: Throttle value, between -1.0 and 1.0
        :type throttle: float
        :param seat: Robot seat
        :type seat: int
        """
        asyncio.run_coroutine_threadsafe(
            self._joystick.handle_coordinates(0, throttle, seat), self._loop
        )

    def threadsafe_steer(self, steering, seat):
        """Threadsafe helper method for using steering

        :param steering: Steering value, between -1.0 and 1.0
        :type steering: float
        :param seat: Robot seat
        :type seat: int
        """
        asyncio.run_coroutine_threadsafe(
            self._joystick.handle_coordinates(steering, 0, seat), self._loop
        )
