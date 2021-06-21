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
    def _get_default_keybinds(self):
        """Returns the default keybind(s) for the input

        Returns the default inputs in the correct format that the protocol
        expects. The format depends on the input type.
        """

    @abstractmethod
    def get_name(self):
        """Returns the name of the input

        :return: name of the input
        :rtype: str
        """
        pass
