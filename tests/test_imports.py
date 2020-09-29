import unittest
import sys
from unittest.mock import Mock


def import_mock_modules(names):
    for name in names:
        sys.modules[name] = Mock()


class ImportTest(unittest.TestCase):
    def test_imports(self):
        """Test that the imports work

        Some external package imports are mocked.
        """

        # DEVICES
        from surrortg.devices.udp import UdpActuator, UdpBot, UdpCar, UdpInput
        from surrortg.devices.udp.udp_protocol import (  # noqa:F811
            open_remote_endpoint,
            open_local_endpoint,
            open_remote_endpoint,
        )

        # INPUTS
        from surrortg.inputs import (
            Input,
            Switch,
            DelayedSwitch,
            Joystick,
            Directions,
            LinearActuator,
        )

        # NETWORK
        from surrortg.network import (
            SocketHandler,
            MessageRouter,
            MultiSeatMessageRouter,
        )

        # ROOT
        from surrortg import Game, GameIO
