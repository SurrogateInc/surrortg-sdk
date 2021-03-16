import sys
import unittest
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
        # ROOT
        from surrortg import Game, GameIO  # noqa:F401
        from surrortg.devices.udp import (  # noqa:F401
            UdpActuator,
            UdpBot,
            UdpCar,
            UdpInput,
        )
        from surrortg.devices.udp.udp_protocol import (  # noqa:F811,F401
            open_local_endpoint,
            open_remote_endpoint,
        )

        # INPUTS
        from surrortg.inputs import (  # noqa:F401
            DelayedSwitch,
            Directions,
            Input,
            Joystick,
            LinearActuator,
            Switch,
        )

        # NETWORK
        from surrortg.network import (  # noqa:F401
            MessageRouter,
            MultiSeatMessageRouter,
            SocketHandler,
        )
