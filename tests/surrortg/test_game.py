import asyncio
import copy
import logging
import os
import time
import unittest
from signal import SIGINT, SIGTERM, SIGUSR1
from threading import Thread

from surrortg import ConfigType, Game, RobotType


class GameTest(unittest.TestCase):
    def test_run_exception(self):
        """
        Make sure that _exit_reason and _exception are correct when run()
        raises an uncaught exception

        EXIT_REASONS = {
            0: "Uncaught exception",
        }
        """

        class GameModRaise(Game):
            """Modded game that raises RuntimeError instead of
            connecting to GE"""

            async def raise_error(self):
                raise RuntimeError

            def run(self):
                self._pre_run(
                    "./tests/test_data/test_config.toml",
                    socketio_logging_level=logging.WARNING,
                    robot_type=RobotType.ROBOT,
                    device_id=None,
                )
                self.io._socket_handler.run = self.raise_error
                self._run()
                self._post_run()

        g = GameModRaise()
        with self.assertRaises(RuntimeError):
            g.run()
        self.assertEqual(g._exit_reason, 0)
        self.assertEqual(type(g._exception), RuntimeError)

    def test_run_signaling(self):
        """
        Make sure that _exit_reason and _exception are correct when run()
        is interrupted or terminated

        EXIT_REASONS = {
            1: "Interrupted (SIGINT)",
            2: "Terminated (SIGTERM)",
            3: "Update (SIGUSR1)",
        }
        """

        # helper methods for sending INT and TERM signals to the Game
        pid = os.getpid()

        def send_signal_when_running(
            signal,
            game,
            post_signal_action=None,
            post_signal_action_param=None,
        ):
            Thread(
                target=_send_signal_thread,
                args=[
                    signal,
                    game,
                    post_signal_action,
                    post_signal_action_param,
                ],
            ).start()

        def _send_signal_thread(
            signal, game, post_signal_action, post_signal_action_param
        ):
            tries = 0
            while game._run_not_called() and tries < 10:
                time.sleep(0.1)
                tries = tries + 1
            os.kill(pid, signal)
            if post_signal_action is not None:
                time.sleep(0.05)
                post_signal_action(post_signal_action_param)

        class GameModWait(Game):
            """Modded game that waits instead of connecting to GE"""

            async def wait(self):
                while True:
                    await asyncio.sleep(1)

            def run(self):
                self._pre_run(
                    "./tests/test_data/test_config.toml",
                    socketio_logging_level=logging.WARNING,
                    robot_type=RobotType.ROBOT,
                    device_id=None,
                )
                self.io._socket_handler.run = self.wait
                self._run()
                self._post_run()

        # case 1: "Interrupted (SIGINT)"
        g = GameModWait()
        send_signal_when_running(SIGINT, g)
        try:
            g.run()
        except Exception as e:
            self.fail(
                f"Game.run() raised unexpected exception {e} when interrupted"
            )
        self.assertEqual(g._exit_reason, 1)
        self.assertEqual(g._exception, None)

        # case 2: "Terminated (SIGTERM)"
        g = GameModWait()
        send_signal_when_running(SIGTERM, g)
        try:
            g.run()
        except Exception as e:
            self.fail(
                f"Game.run() raised unexpected exception {e} when terminated"
            )
        self.assertEqual(g._exit_reason, 2)
        self.assertEqual(g._exception, None)

        # case 3: "Update (SIGUSR1)"
        g = GameModWait()
        send_signal_when_running(
            SIGUSR1,
            g,
            post_signal_action=g._exit_signal_handler,
            post_signal_action_param=3,
        )
        try:
            g.run()
        except Exception as e:
            self.fail(
                f"Game.run() raised unexpected exception {e} when terminated"
            )
        self.assertEqual(g._exit_reason, 3)
        self.assertEqual(g._exception, None)

    def test_run_logging(self):
        """Make sure game loop logs are shown but only if no custom implementation
        is present"""

        # test that everything is logged when nothing is implemented
        with self.assertLogs(level="DEBUG") as cm:
            g = Game()
            g._pre_run(
                "./tests/test_data/test_config.toml",
                socketio_logging_level=logging.WARNING,
                robot_type=RobotType.ROBOT,
                device_id=None,
            )  # this simulates run(), really only part of it
            self.assertEqual(
                cm.output,
                [
                    "DEBUG:root:on_init not implemented. No inputs/outputs were registered.",  # noqa: E501
                    "DEBUG:root:on_config not implemented. Using the current set.",  # noqa: E501
                    "DEBUG:root:on_prepare not implemented.",
                    "DEBUG:root:on_pre_game not implemented.",
                    "DEBUG:root:on_countdown not implemented.",
                    "DEBUG:root:on_start not implemented.",
                    "DEBUG:root:on_finish not implemented.",
                    "DEBUG:root:on_exit not implemented.",
                ],
            )

        # test that if certain methods are implemented, they are not logged"
        class GameModSomeImplemented(Game):
            """Modded game that has a custom implementation for
            on_config and on_start"""

            async def on_config(self, configs):
                print("custom")

            async def on_start(self, configs, players):
                pass

        with self.assertLogs(level="DEBUG") as cm:
            g = GameModSomeImplemented()
            g._pre_run(
                "./tests/test_data/test_config.toml",
                socketio_logging_level=logging.WARNING,
                robot_type=RobotType.ROBOT,
                device_id=None,
            )  # this simulates run(), really only part of it
            self.assertEqual(
                cm.output,
                [
                    "DEBUG:root:on_init not implemented. No inputs/outputs were registered.",  # noqa: E501
                    "DEBUG:root:on_prepare not implemented.",
                    "DEBUG:root:on_pre_game not implemented.",
                    "DEBUG:root:on_countdown not implemented.",
                    "DEBUG:root:on_finish not implemented.",
                    "DEBUG:root:on_exit not implemented.",
                ],
            )

    def test_game_io_register_inputs(self):
        """self.io should raise RuntimeError if called before run(),
        but not if called afterwards"""

        # test premature calling (run not called)
        g = Game()
        with self.assertRaises(RuntimeError):
            g.io.register_inputs({})

        # test premature calling
        # (run called, but io._can_register_inputs is not set)
        g = Game()
        g._pre_run(
            "./tests/test_data/test_config.toml",
            socketio_logging_level=logging.WARNING,
            robot_type=RobotType.ROBOT,
            device_id=None,
        )  # this simulates run(), really only part of it
        with self.assertRaises(RuntimeError):
            g.io.register_inputs({})

        # test the correct use
        g = Game()
        g._pre_run(
            "./tests/test_data/test_config.toml",
            socketio_logging_level=logging.WARNING,
            robot_type=RobotType.ROBOT,
            device_id=None,
        )  # this simulates run(), really only part of it
        g.io._can_register_inputs = True
        try:
            g.io.register_inputs({})
        except RuntimeError:
            self.fail("io.register_inputs() raised an unexpected RuntimeError")

    def test_game_io_register_config(self):
        # test premature calling (run not called)
        g = Game()
        with self.assertRaises(RuntimeError):
            g.io.register_config(
                "testconfig", ConfigType.STRING, "defaultval", True
            )

        # test premature calling
        # (run called, but io._can_register_inputs is not set)
        g = Game()
        g._pre_run(
            "./tests/test_data/test_config.toml",
            socketio_logging_level=logging.WARNING,
            robot_type=RobotType.ROBOT,
            device_id=None,
        )  # this simulates run(), really only part of it
        with self.assertRaises(RuntimeError):
            g.io.register_config(
                "testconfig", ConfigType.STRING, "defaultval", True
            )

        # test the correct use
        g = Game()
        g._pre_run(
            "./tests/test_data/test_config.toml",
            socketio_logging_level=logging.WARNING,
            robot_type=RobotType.ROBOT,
            device_id=None,
        )  # this simulates run(), really only part of it
        g.io._can_register_configs = True
        try:
            g.io.register_config(
                "teststring", ConfigType.STRING, "defaultval", True
            )
            g.io.register_config("testnumber", ConfigType.NUMBER, 2.1, True)
            g.io.register_config("testinteger", ConfigType.INTEGER, 3, True)
            g.io.register_config("testboolean", ConfigType.BOOLEAN, True, True)
            g.io.register_config("testglobal", ConfigType.BOOLEAN, True, False)
            g.io.register_config(
                "testminmaxint",
                ConfigType.INTEGER,
                3,
                False,
                minimum=1,
                maximum=5,
            )
            g.io.register_config(
                "testminmaxfloat",
                ConfigType.NUMBER,
                4,
                False,
                minimum=1.2,
                maximum=5.3,
            )
            g.io.register_config(
                "testenumint",
                ConfigType.INTEGER,
                3,
                False,
                enum=[1, 5, 2, 3],
            )
            g.io.register_config(
                "testenumstring",
                ConfigType.STRING,
                "defaultval",
                True,
                enum=["defaultval", "otherval"],
            )
        except RuntimeError:
            self.fail("io.register_config() raised an unexpected RuntimeError")

        # test wrong config combinations
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "mismatchingdefault", ConfigType.STRING, 3, True
            )
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "stringmin", ConfigType.STRING, 3, True, minimum="what?"
            )
        with self.assertRaises(AssertionError):
            g.io.register_config("floatint", ConfigType.INTEGER, 3.2, True)
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "floatintmax", ConfigType.INTEGER, 3, True, maximum=5.1
            )
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "inttoolarge", ConfigType.INTEGER, 6, True, maximum=5
            )
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "minmaxandenum",
                ConfigType.INTEGER,
                6,
                True,
                maximum=5,
                enum=[5, 6],
            )
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "enumwrongtype", ConfigType.INTEGER, 6, True, enum=["string"]
            )
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "enummixedtypes",
                ConfigType.INTEGER,
                6,
                True,
                enum=[6, 5, "string"],
            )
        with self.assertRaises(AssertionError):
            g.io.register_config(
                "defaultnotinenum", ConfigType.INTEGER, 6, True, enum=[3, 5]
            )

        test_conf = {
            "children": {
                "gameconf": {
                    "title": "Test game",
                    "description": "Describes the conf in detail",
                    "valueType": ConfigType.NUMBER,
                    "default": 1,
                    "enum": [
                        {
                            "value": 1,
                            "description": "desc",
                        },
                        {"value": 2, "description": "luls"},
                    ],
                },
                "gamecond": {
                    "title": "Conditional shit",
                    "description": "wut",
                    "valueType": ConfigType.BOOLEAN,
                    "default": False,
                    "conditions": [
                        {"variable": "gameconf", "value": 1},
                    ],
                },
                "mygroup": {
                    "conditions": [
                        {"variable": "gamecond", "value": True},
                    ],
                    "children": {
                        "mysubconf": {
                            "title": "My Sub Conf",
                            "valueType": ConfigType.INTEGER,
                            "default": 3,
                            "minimum": 2,
                            "maximum": 50,
                        },
                        "subconf2": {
                            "title": "Sub bool",
                            "valueType": ConfigType.BOOLEAN,
                            "default": False,
                        },
                    },
                },
            }
        }
        try:
            g.io.set_robot_configs(copy.deepcopy(test_conf))
            g.io.set_game_configs(copy.deepcopy(test_conf))
        except Exception:
            self.fail("set_config raised an unexpected exception")

        test_copy = copy.deepcopy(test_conf)
        test_copy["children"]["gameconf"]["extra"] = 0
        with self.assertRaises(AssertionError):
            g.io.set_robot_configs(test_copy)
        test_copy = copy.deepcopy(test_conf)
        test_copy["children"]["gameconf"]["default"] = False
        with self.assertRaises(AssertionError):
            g.io.set_robot_configs(test_copy)

    def test_game_properties(self):
        """The properties should raise RuntimeError if accessed before run"""

        g = Game()

        # before run(), everything should raise RuntimeError
        with self.assertRaises(RuntimeError):
            g.io
        with self.assertRaises(RuntimeError):
            g.configs
        with self.assertRaises(RuntimeError):
            g.players

        # after run(), io should not raise RuntimeError
        g._pre_run(
            "./tests/test_data/test_config.toml",
            socketio_logging_level=logging.WARNING,
            robot_type=RobotType.ROBOT,
            device_id=None,
        )  # this simulates run(), really only part of it
        try:
            g.io
        except RuntimeError:
            self.fail("io raised an unexpected RuntimeError")

        # configs and players should still raise RuntimeError
        with self.assertRaises(RuntimeError):
            g.configs
        with self.assertRaises(RuntimeError):
            g.players

        # but not after they have gotten some value from GE
        g._configs = {}
        g._players = {}
        try:
            g.configs
            g.players
        except RuntimeError:
            self.fail("players or configs raised an unexpected RuntimeError")
