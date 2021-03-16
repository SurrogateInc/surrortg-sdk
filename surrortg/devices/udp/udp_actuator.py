import asyncio
import logging
import struct

from ...inputs import LinearActuator
from .udp_input import UdpInput


class UdpActuator(LinearActuator, UdpInput):
    """Class for udp-controlled actuator.

    :param cmd: udp byte that identifies the control id
    :type cmd: int
    :param multiplier: multiplier of the value, defaults to 1.0
    :type multiplier: float, optional
    :param repeat_commands: defines if commands should be repeated,
        defaults to False
    :type repeat_commands: bool, optional
    """

    def __init__(self, cmd, multiplier=1.0, repeat_commands=False):
        super().__init__()
        self.cmd = cmd
        self.multiplier = multiplier
        self.middle = 100
        self.range = 100
        self.should_repeat = repeat_commands
        self.current_val = self.middle
        self.repeat_task = None

    async def drive_actuator(self, val, seat, unscaled=False):
        """Drive actuator by sending value as a udp command

        :param val: actuator position value, between -1.0 and 1.0
        :type val: float
        :param seat: Robot seat
        :type seat: int
        :param unscaled: defines if value should be unscaled, defaults to False
        :type unscaled: bool, optional
        """
        if not unscaled:
            val = val * self.multiplier
        self._send_command(val, seat)
        if self.should_repeat:
            self.current_val = val
            if self.repeat_task is not None:
                self.repeat_task.cancel()
            self.repeat_task = asyncio.create_task(
                self._repeat_command(10, 0.2, seat)
            )

    def _send_command(self, val, seat):
        """Sends a udp command to the endpoint of the seat

        :param val: actuator position value, between -1.0 and 1.0
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

        diff = val * self.range

        actuator_val = int(self.middle + diff)
        logging.debug(
            f"Running udp actuator {self.cmd} of seat {seat}"
            f"with pwm={actuator_val} value={val}"
        )
        if not endpoint.closed:
            try:
                endpoint.send(struct.pack("BB", self.cmd, actuator_val))

            except OSError as e:
                logging.warning(
                    f"Failed to send value {val} to seat {seat} "
                    f"command {self.cmd}: {e}"
                )
        else:
            logging.debug(
                f"Did not send value {val} to seat {seat} "
                f"command {self.cmd}, was closed"
            )

    async def _repeat_command(self, num_sends, interval, seat):
        """Calls _send_command on repeat a specific number of times

        :param num_sends: number of times _send_command is called
        :type num_sends: int
        :param interval: number of seconds between command sends
        :type interval: float
        :param seat: Robot seat
        :type seat: int
        """
        for _ in range(num_sends):
            await asyncio.sleep(interval)
            self._send_command(self.current_val, seat)
