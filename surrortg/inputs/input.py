from abc import ABC, abstractmethod


class Input(ABC):
    """Base class for all user inputs"""

    @abstractmethod
    async def _on_input(self, command, seat):
        """Implements the spesific Input functionality

        :param command: Command from the game engine
        :type command: dict
        :param seat: Robot seat
        :type seat: int
        """
        pass

    @abstractmethod
    async def reset(self, seat):
        """Reset functionality for the Input

        :param seat: Robot seat
        :type seat: int
        """
        pass

    async def shutdown(self, seat):
        """Input shutdown method. Defaults to calling reset.

        :param seat: Robot seat
        :type seat: int
        """
        await self.reset(seat)

    @abstractmethod
    def get_name(self):
        """Returns the name of the input

        :return: name of the input
        :rtype: str
        """
        pass
