import logging
import struct

from surrortg.inputs import Switch

from .tcp_input import TcpInput
from .tcp_protocol import TcpCommandId


class TcpSwitch(Switch, TcpInput):
    """Class for tcp-controlled switch.

    :param cmd: Byte that identifies the control id
    :type cmd: TcpCommandId or int
    """

    def __init__(self, cmd):
        assert isinstance(
            cmd, (int, TcpCommandId)
        ), "cmd must be int or TcpCommandId"
        super().__init__()
        self._cmd = int(cmd)
        self._value_off = 0
        self._value_on = 1

    async def on(self, seat):
        await self._send_command(self._value_on, seat)

    async def off(self, seat):
        await self._send_command(self._value_off, seat)

    async def _send_command(self, val, seat):
        """Sends a tcp command to the endpoint of the seat

        :param val: switch position value, 0 or 1
        :type val: int
        :param seat: Robot seat
        :type seat: int
        """
        assert val == 0 or val == 1

        if seat not in self.endpoints:
            logging.warning(
                f"Endpoint not found for seat {seat}, not sending command."
            )
            return

        endpoint = self.endpoints[seat]

        logging.debug(
            f"Running tcp switch cmd {self._cmd}, seat {seat} with value {val}"
        )
        if not endpoint.closed:
            try:
                await endpoint.send(struct.pack("BB", self._cmd, val))
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
