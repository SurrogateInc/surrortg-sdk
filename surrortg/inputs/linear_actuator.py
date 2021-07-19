import logging
import traceback
from abc import abstractmethod

from .input import Input


class LinearActuator(Input):
    """A class for moving linear actuators"""

    async def _on_input(self, command, seat):
        """LinearActuator input functionality

        Parses actuator value from command and drives the actuator
        to the correct value.
        :param command: Command from game engine
        :type command: dict
        :param seat: Robot seat
        :type seat: int
        """
        if "val" not in command:
            logging.warning("Received malformed command for LinearActuator")
            return

        try:
            val = float(command["val"])
            if val < -1.0 or val > 1.0:
                logging.warning(
                    "Received invalid value [%d] for LinearActuator", val
                )
                return
            await self.drive_actuator(val, seat)
        except (ValueError, TypeError):
            logging.warning(
                "Could not convert command for LinearActuator into float %s"
                % traceback.format_exc()
            )

    @abstractmethod
    async def drive_actuator(self, val, seat):
        """Drive actuator to parameter val

        :param val: actuator position value, must be between -1.0 and 1.0
        :type val: float
        :param seat: Robot seat
        :type seat: int
        """
        pass

    async def reset(self, seat):
        """LinearActuator reset functionality

        Defaults to driving the actuator to value 0

        :param seat: Robot seat
        :type seat: int
        """
        await self.drive_actuator(0, seat)

    def get_name(self):
        """Returns the name of the input

        :return: name of the input
        :rtype: str
        """
        return "linearActuator"

    def _stringify_keybinds(self, binds):
        def enum_to_str(item):
            if type(item) is not str:
                return item.value
            return item

        for k, v in binds.items():
            binds[k] = enum_to_str(v)

    def _get_default_keybinds(self):
        binds = self.get_default_keybinds()
        max_keys = []
        min_keys = []

        def append_keys(keys):
            if "min" in keys:
                min_keys.append(keys["min"])
            if "max" in keys:
                max_keys.append(keys["max"])

        if isinstance(binds, list):
            for item in binds:
                self._stringify_keybinds(item)
                append_keys(item)
        else:
            self._stringify_keybinds(binds)
            append_keys(item)

        key_msg = {
            "minKeys": {
                "keys": min_keys,
                "humanReadableName": "min",
            },
            "maxKeys": {
                "keys": max_keys,
                "humanReadableName": "max",
            },
        }

        return key_msg

    def get_default_keybinds(self):
        """Return a dict or list of dicts with keybinds.

        Linear actuators are bound to W and S keys by default.

        To override the defaults, override this method in your linear actuator
        subclass and return different keybinds.
        """
        return [
            {
                "min": "KeyW",
                "max": "KeyS",
            }
        ]
