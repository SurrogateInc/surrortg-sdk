import logging
from abc import abstractmethod

from .input import Input
from .input_config import assert_keycode_list


class Switch(Input):
    """Switch input class

    Implement custom on() and off() logic
    Read more about defaults from input_config.py
    """

    def validate_defaults(self, defaults):
        super().validate_defaults(defaults)
        assert defaults.keys() <= {
            "humanReadableName",
            "onScreenPosition",
            "keys",
        }, "there were extra items in defaults"
        assert "keys" in defaults
        assert_keycode_list(defaults["keys"])

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

    def _get_default_keybinds(self):
        binds = self.get_default_keybinds()

        if not isinstance(binds, list):
            binds = [binds]

        def enum_to_str(item):
            if type(item) is not str:
                return item.value
            return item

        binds = list(map(enum_to_str, binds))

        return {"keys": binds}

    def get_default_keybinds(self):
        """Returns a single keybind or a list of keybinds.

        Switches are bound to the space key by default.

        To override the defaults, override this method in your switch
        subclass and return different keybinds.
        """
        return []
