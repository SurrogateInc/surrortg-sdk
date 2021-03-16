import logging
import os
import socket

import toml

REQUIRED_CONFIG_KEYS = ["device_id", "game_engine"]
REQUIRED_CONFIG_GE_KEYS = ["url", "token"]


def get_config(config_path, default_config_path="/etc/srtg/srtg.toml"):
    """A separate static method makes testing easier"""
    if config_path is None:
        config_path = default_config_path

    # make sure that the main config file exists
    if not os.path.isfile(config_path):
        raise RuntimeError(f"Config file '{config_path}' does not exist")

    # get configs
    config = toml.load(config_path)
    # add ["game_engine"] if did not exist already
    if "game_engine" not in config:
        config["game_engine"] = toml.load(
            _get_current_ge_config_path(default_config_path)
        )["game_engine"]

    # validate config
    _validate_config(config, config_path)

    device_id = config["device_id"]
    if not device_id:
        logging.info("Using hostname as device_id")
        config["device_id"] = socket.gethostname().split(".", 1)[0]

    if "id" not in config["game_engine"]:
        raw_token = config["game_engine"]["token"]
        if "/" not in raw_token:
            raise RuntimeError(
                "Malformed token: are you using old token format?"
            )
        tokens = raw_token.split("/")
        config["game_engine"]["id"] = tokens[0]
        config["game_engine"]["token"] = tokens[1]
    else:
        if "/" in config["game_engine"]["token"]:
            raise RuntimeError(
                "Trying to use new combined token with separate id"
            )

    return config


def _get_current_ge_config_path(
    default_config_path,
    current_ge_name_file="/var/lib/srtg/current_game_engine",
):
    """A separate static method makes testing easier"""

    # get the current game engine name, and return the path to it
    config_file_parent_dir = os.path.dirname(default_config_path)
    try:
        with open(current_ge_name_file) as f:
            return (
                f"{config_file_parent_dir}/game_engines/"
                f"{f.readline().rstrip()}.toml"
            )
    except Exception:
        logging.warning(
            "Could not read the current game engine name from "
            f"'{current_ge_name_file}'\nAdd correct name there "
            "or add [game_engine] section to config"
        )
        raise


def _validate_config(config, config_path):
    """A separate static method makes testing easier"""
    for key in REQUIRED_CONFIG_KEYS:
        assert (
            key in config
        ), f"Required '{key}' not found from config: '{config_path}'"
    for key in REQUIRED_CONFIG_GE_KEYS:
        assert key in config["game_engine"], (
            f"Required '{key}' not found from config['game_engine']: "
            f"'{config_path}'"
        )
