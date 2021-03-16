import logging
from abc import abstractmethod

from .input import Input


class Switch(Input):
    """Switch input class

    Implement custom on() and off() logic
    """

    async def _on_input(self, command, seat):
        """Switch input functionality

        Calls on and off depending on command state
        :param command: Command from game engine
        :type command: dict
        :param seat: Robot seat
        :type seat: int
        """
        if "state" not in command:
            logging.warning("Switch: invalid command received")
            return

        try:
            val = str(command["state"])
        except (ValueError, TypeError):
            logging.warn(
                f"Switch: could not convert {command['state']} into String"
            )
            return

        if val != "up" and val != "down":
            logging.warn("Switch: command not <up|down>")
            return

        if val == "up":
            await self.off(seat)
        else:
            await self.on(seat)

    @abstractmethod
    async def on(self, seat):
        """Switch turned on functionality

        :param seat: Robot seat
        :type seat: int
        """
        pass

    @abstractmethod
    async def off(self, seat):
        """Switch turned off functionality

        :param seat: Robot seat
        :type seat: int
        """
        pass

    async def reset(self, seat):
        """Switch reset functionality

        Defaults to calling off()

        :param seat: Robot seat
        :type seat: int
        """
        await self.off(seat)

    def get_name(self):
        """Returns the name of the input

        :return: name of the input
        :rtype: str
        """
        return "button"
