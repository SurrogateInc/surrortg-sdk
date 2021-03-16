import unittest

import toml

from surrortg import get_config
from surrortg.config_parser import (
    _get_current_ge_config_path,
    _validate_config,
)


class GameIOTest(unittest.TestCase):
    def test_get_config(self):
        test_config = toml.load("./tests/test_data/test_config.toml")

        # test that finds the default one
        self.assertEqual(
            get_config("./tests/test_data/test_config.toml"),
            test_config,
        )

        # test that fails for non-existent config
        with self.assertRaises(RuntimeError):
            get_config("./tests/test_data/NON-EXISTENT.toml")

    def test_get_current_ge_config_path(self):
        # test that finds the current game engine path
        self.assertEqual(
            _get_current_ge_config_path(
                default_config_path="./tests/test_data/test_config_no_ge.toml",
                current_ge_name_file=(
                    "./tests/test_data/test_config_no_ge.toml"
                ),
            ),
            './tests/test_data/game_engines/device_id = "testrobot".toml',
        )

        # test that fails for non-existent current GE name file
        with self.assertRaises(FileNotFoundError):
            _get_current_ge_config_path(
                default_config_path="./tests/test_data/test_config_no_ge.toml",
                current_ge_name_file="./tests/test_data/NON-EXISTENT",
            )

    def test_validate_config(self):
        def config_without_key(key):
            new_config = toml.load("./tests/test_data/test_config.toml")
            new_config.pop(key)
            return new_config

        def config_without_ge_key(key):
            new_config = toml.load("./tests/test_data/test_config.toml")
            new_config["game_engine"].pop(key)
            return new_config

        # check that no assertionError with valid config
        _validate_config(toml.load("./tests/test_data/test_config.toml"), None)

        # test the error cases
        with self.assertRaises(AssertionError):
            _validate_config(config_without_key("device_id"), None)
        with self.assertRaises(AssertionError):
            _validate_config(config_without_key("game_engine"), None)
        with self.assertRaises(AssertionError):
            _validate_config(config_without_ge_key("url"), None)
        with self.assertRaises(AssertionError):
            _validate_config(config_without_ge_key("token"), None)
