import logging
import struct

from surrortg.inputs import LinearActuator

from .tcp_input import TcpInput
from .tcp_protocol import TcpCommandId


class TcpActuator(LinearActuator, TcpInput):
    """Class for tcp-controlled actuator.

    :param cmd: Byte that identifies the control id
    :type cmd: TcpCommandId or int
    :param multiplier: Multiplier of the value, defaults to 1.0
    :type multiplier: float, optional
    """

    def __init__(self, cmd, multiplier=1.0):
        assert isinstance(
            cmd, (int, TcpCommandId)
        ), "cmd must be int or TcpCommandId"
        super().__init__()
        self._cmd = int(cmd)
        self._multiplier = multiplier
        self._middle = 100
        self._range = 100
        self._current_val = self._middle

    async def drive_actuator(self, val, seat, unscaled=False):
        """Drive actuator by sending value as a tcp command

        :param val: Actuator position value, between -1.0 and 1.0
        :type val: float
        :param seat: Robot seat
        :type seat: int
        :param unscaled: Defines if value should be unscaled, defaults to False
        :type unscaled: bool, optional
        """
        if not unscaled:
            val = val * self._multiplier
        await self._send_command(val, seat)

    async def _send_command(self, val, seat):
        """Sends a tcp command to the endpoint of the seat

        :param val: Actuator position value, between -1.0 and 1.0
        :type val: float
        :param seat: Robot seat
        :type seat: int
        """
        assert -1.0 <= val <= 1.0

        try:
            endpoint = self.endpoints[seat]
        except KeyError:
            logging.warning(
                f"Endpoint not found for seat {seat}, not sending command."
            )
            return

        diff = val * self._range

        actuator_val = int(self._middle + diff)
        logging.debug(
            f"Running udp actuator {self._cmd} of seat {seat}"
            f"with pwm={actuator_val} value={val}"
        )
        if not endpoint.closed:
            try:
                await endpoint.send(struct.pack("BB", self._cmd, actuator_val))

            except OSError as e:
                logging.warning(
                    f"Failed to send value {val} to seat {seat} "
                    f"command {self._cmd}: {e}"
                )
        else:
            logging.debug(
                f"Did not send value {val} to seat {seat} "
                f"command {self._cmd}, was closed"
            )
