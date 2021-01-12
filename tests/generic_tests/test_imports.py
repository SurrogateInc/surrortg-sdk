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
        from surrortg.devices.udp import (  # noqa:F401
            UdpActuator,
            UdpBot,
            UdpCar,
            UdpInput,
        )
        from surrortg.devices.udp.udp_protocol import (  # noqa:F811,F401
            open_remote_endpoint,
            open_local_endpoint,
            open_remote_endpoint,
        )

        # INPUTS
        from surrortg.inputs import (  # noqa:F401
            Input,
            Switch,
            DelayedSwitch,
            Joystick,
            Directions,
            LinearActuator,
        )

        # NETWORK
        from surrortg.network import (  # noqa:F401
            SocketHandler,
            MessageRouter,
            MultiSeatMessageRouter,
        )

        # ROOT
        from surrortg import Game, GameIO  # noqa:F401
