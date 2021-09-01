from abc import ABC, abstractmethod

from .input_config import assert_on_screen_position, convert_enums_to_values


class Input(ABC):
    """Base class for all user inputs"""

    def __init__(self, defaults=None):
        if defaults:
            self.validate_defaults(defaults)
        self.defaults = defaults

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

    def validate_defaults(self, defaults):
        assert isinstance(defaults, dict), "defaults needs to be dictionary"
        assert "humanReadableName" not in defaults or isinstance(
            defaults["humanReadableName"], str
        ), "humanReadableName must be a string"
        if "onScreenPosition" in defaults:
            assert_on_screen_position(defaults["onScreenPosition"])

    def get_defaults_dict(self):
        """Returns the default input config"""
        if self.defaults:
            return convert_enums_to_values(self.defaults)
        return self._get_default_keybinds()

    @abstractmethod
    def get_name(self):
        """Returns the name of the input

        :return: name of the input
        :rtype: str
        """
        pass
