import asyncio
import logging
import struct

from surrortg.inputs import Switch

from . import UdpInput


class UdpSwitch(Switch, UdpInput):
    """Class for udp-controlled switch.

    :param cmd: udp byte that identifies the control id
    :type cmd: int
    :param multiplier: multiplier of the value, defaults to 1.0
    :type multiplier: float, optional
    :param repeat_commands: defines if commands should be repeated,
        defaults to False
    :type repeat_commands: bool, optional
    """

    def __init__(self, cmd, repeat_commands=False):
        super().__init__()
        self.cmd = cmd
        self.value_off = 0
        self.value_on = 1
        self.should_repeat = repeat_commands
        self.current_val = self.value_off
        self.repeat_task = None

    async def on(self, seat):
        self._handle_command(self.value_on, seat)

    async def off(self, seat):
        self._handle_command(self.value_off, seat)

    def _handle_command(self, val, seat):
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
            f"Running udp switch {self.cmd} of seat {seat} with value {val}"
        )
        if not endpoint.closed:
            try:
                endpoint.send(struct.pack("BB", self.cmd, val))

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
