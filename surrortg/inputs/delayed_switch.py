import logging
from abc import abstractmethod

from .input import Input


class DelayedSwitch(Input):
    """A class for using a switch with a delay"""

    async def _on_input(self, command, seat):
        """DelayedSwitch input functionality

        :param command: Command from game engine
        :type command: dict
        :param seat: Robot seat
        :type seat: int
        """
        if "state" not in command or "delay" not in command:
            logging.warning("Received invalid command for DelayedSwitch")
            return

        try:
            val = str(command["state"])
            if val != "up" and val != "down":
                logging.warn("Button command not <up|down>")
                return
            delay = int(command["delay"])
            await self.set_state(val, delay, seat)
        except (ValueError, TypeError):
            logging.warn(
                "Could not convert command for Button into bool: %s"
                % command["state"]
            )

    @abstractmethod
    async def set_state(self, state, delay, seat):
        """Set switch to 'up' or 'down' state after a user implemented delay

        :param state: 'up' or 'down'
        :type state: str
        :param delay: User implemented delay amount in seconds
        :type delay: float
        :param seat: Robot seat
        :type seat: int
        """
        pass

    async def reset(self, seat):
        """DelayedSwitch reset functionality

        Defaults to setting the switch state to up

        :param seat: Robot seat
        :type seat: int
        """
        self.set_state("up", 0, seat)

    def get_name(self):
        """Returns the name of the input

        :return: name of the input
        :rtype: str
        """
        return "delayedButton"
