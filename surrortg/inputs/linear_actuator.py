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
