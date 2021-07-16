from surrortg.inputs import Joystick

from .tcp_actuator import TcpActuator
from .tcp_input import TcpInput


class TcpJoystick(Joystick, TcpInput):
    """Class for TCP-controlled joystick

    :param cmd_x: Byte that identifies the control id for x-axis
    :type cmd_x: TcpCommandId or int
    :param cmd_y: Byte that identifies the control id for y-axis
    :type cmd_y: TcpCommandId or int
    :param multiplier_x: Multiplier of the x-axis value, defaults to 1.0
    :type multiplier_x: float, optional
    :param multiplier_y: Multiplier of the y-axis value, defaults to 1.0
    :type multiplier_y: float, optional
    """

    def __init__(self, cmd_x, cmd_y, multiplier_x=1.0, multiplier_y=1.0):
        super().__init__()
        self._actuator_x = TcpActuator(cmd_x, multiplier_x)
        self._actuator_y = TcpActuator(cmd_y, multiplier_y)

    async def handle_coordinates(self, x, y, seat=0):
        await self._actuator_x.drive_actuator(x, seat)
        await self._actuator_y.drive_actuator(y, seat)

    def set_endpoints(self, endpoints):
        self._actuator_x.set_endpoints(endpoints)
        self._actuator_y.set_endpoints(endpoints)
