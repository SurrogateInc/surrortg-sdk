import logging
import toml
import os.path
import socket
from .network.socket_handler import SocketHandler
from .network.message_router import MultiSeatMessageRouter

REQUIRED_CONFIG_KEYS = ["device_id", "game_engine"]
REQUIRED_CONFIG_GE_KEYS = ["url", "token"]
SURRORTG_VERSION = "0.2.0"
LOCAL_SOCKET_NAME = "/tmp/.srtg-sock"
DATACHANNEL_CONFIG_KEY = "datachannel"


class GameIO:
    """For communication between Python and the game engine

    The class is accessed through Game.io.
    """

    def __init__(
        self,
        ge_message_handler,
        robot_log_handler,
        config_path,
        socketio_logging_level,
        robot_type,
    ):
        self._config = self._get_config(config_path)

        if "id" not in self._config["game_engine"]:
            raw_token = self._config["game_engine"]["token"]
            if "/" not in raw_token:
                raise RuntimeError(
                    "Malformed token: are you using old token format?"
                )
            tokens = raw_token.split("/")
            self._config["game_engine"]["id"] = tokens[0]
            self._config["game_engine"]["token"] = tokens[1]
        else:
            if "/" in self._config["game_engine"]["token"]:
                raise RuntimeError(
                    "Trying to use new combined token with separate id"
                )

        device_id = self._config["device_id"]
        if not device_id:
            logging.info("Using hostname as device_id")
            device_id = socket.gethostname().split(".", 1)[0]

        self._socket_handler = SocketHandler(
            self._config["game_engine"]["url"],
            query={
                "clientType": "robot",
                "robotType": robot_type,
                "robotVersion": SURRORTG_VERSION,
                "clientId": device_id,
                "gameId": self._config["game_engine"]["id"],
                "token": self._config["game_engine"]["token"],
            },
            local_socket_name=LOCAL_SOCKET_NAME
            if self._config.get(DATACHANNEL_CONFIG_KEY, False)
            else None,
            socketio_logging_level=socketio_logging_level,
        )
        self._socket_handler.register_on_message_cb(ge_message_handler)
        self._socket_handler.register_on_message_response_cb(
            ge_message_handler, self._is_config_message
        )
        self._message_router = MultiSeatMessageRouter(robot_log_handler)
        self._socket_handler.register_on_message_cb(
            self._message_router.handle_message
        )
        self._socket_handler.register_on_connect_cb(self.provide_inputs)
        self.input_bindings = {}

    def _get_config(
        self, config_path, default_config_path="/etc/srtg/srtg.toml"
    ):
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
                self._get_current_ge_config_path(default_config_path)
            )["game_engine"]

        # validate config
        self._validate_config(config, config_path)

        return config

    @staticmethod
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

    @staticmethod
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

    def _is_config_message(self, message):
        return message.src == "gameEngine" and message.event == "config"

    async def provide_inputs(self):
        bindings = []
        for commandId, obj in self.input_bindings.items():
            bindings.append({"commandId": commandId, **obj})
        self._send_threadsafe("robotInputs", payload=bindings)

    def register_inputs(self, inputs, admin=False, bindable=True):
        """Registers inputs

        Input names must be unique.
        If the same input name already exists, error is risen.

        :param inputs: A dictionary of input device names and objects.
        :type inputs: dict{String: Input}
        :raises RuntimeError if input names are not unique
        :param admin: Describes if the input is for admin use only,
         defaults to False
        :type admin: bool, optional
        :param bindable: Describes if the input can be bound to user
        input. Defaults to True.
        """
        for input_id, handler_obj in inputs.items():
            if input_id in self.input_bindings:
                raise RuntimeError(f"Duplicate input_ids: {input_id}")
            self._message_router.register_input(input_id, handler_obj, admin)
            if bindable:
                self.input_bindings[input_id] = {
                    "type": handler_obj.get_name(),
                    "admin": admin,
                }

    def enable_inputs(self):
        """Enable all registered inputs
        """
        self._message_router.set_enabled_all(True)

    def disable_inputs(self):
        """Disable all registered inputs
        """
        self._message_router.set_enabled_all(False)

    def enable_input(self, seat):
        """Enable a single registered input

        :param seat: Robot seat
        :type seat: int
        """
        self._message_router.set_enabled_seat(seat, True)

    def disable_input(self, seat):
        """Disable a single registered input

        :param seat: Robot seat
        :type seat: int
        """
        self._message_router.set_enabled_seat(seat, False)

    async def reset_inputs(self, seat=None):
        """Reset registered inputs

        If seat is not defined, resets all registered inputs,
        otherwise affects only the inputs with specified seat.

        :param seat: seat number, defaults to None
        :type seat: Int, optional
        """
        # get router and all registered seats
        router = self._message_router.router
        registered_seats = self._message_router.get_all_seats()
        # return if seat is not specified or not found
        if seat is not None and seat not in registered_seats:
            logging.warning(f"Cannot reset inputs for seat {seat}")
            return
        # reset all inputs in router for a specific seat,
        # or all seats if seat is not defined
        for input_ in router.inputs.values():
            if seat is not None:
                await input_.dev.reset(seat)
            else:
                for current_seat in registered_seats:
                    await input_.dev.reset(current_seat)

    async def shutdown_inputs(self, seat=None):
        """Shutdown registered inputs

        If seat is not defined, shuts down all registered inputs,
        otherwise affects only the inputs with specified seat.

        :param seat: seat number, defaults to None
        :type seat: Int, optional
        """
        # get router and all registered seats
        router = self._message_router.router
        registered_seats = self._message_router.get_all_seats()
        # return if seat is not spesified or not found
        if seat is not None and seat not in registered_seats:
            logging.warning(f"Cannot shutdown inputs for seat {seat}")
            return
        # shutdown all inputs in router for a specific seat,
        # or all seats if seat is not defined
        for input_ in router.inputs.values():
            if seat is not None:
                await input_.dev.shutdown(seat)
            else:
                for current_seat in registered_seats:
                    await input_.dev.shutdown(current_seat)

    def send_lap(self, seat=0):
        """Send a lap update to the game engine when lap is finished

        :param seat: seat number, defaults to 0
        :type seat: int, optional
        """
        assert isinstance(seat, int), "seat must be int"
        self._send_threadsafe("lapDone", seat=seat)

    def send_progress(self, progress, seat=0):
        """Send a progress update to the game engine

        :param progress: progress amount between 0 and 1
        :type progress: float
        :param seat: seat number, defaults to 0
        :type seat: int, optional
        """
        assert isinstance(
            progress, (int, float)
        ), "progress must be int or float"
        assert isinstance(seat, int), "seat must be int"
        assert (
            0.0 <= progress and progress <= 1.0
        ), f"progress must be between 0-1, was {progress}"
        self._send_threadsafe("progress", seat=seat, payload={"val": progress})

    def send_score(
        self,
        score=None,
        scores=None,
        seat=0,
        final_score=False,
        seat_final_score=False,
    ):
        """Send a score update to the game engine

        Send eiher a single score or multiple scores.

        :param score: score value, defaults to None
        :type score: int/float, optional
        :param scores: scores dictionary or list, defaults to None
        :type scores: dict/list, optional
        :param seat: seat number, used only with a singe score, defaults to 0
        :type seat: int, optional
        :param final_score: signal to GE that there will not be more scores
            coming, defaults to False
        :type final_score: bool, optional
        :param seat_final_score: signal to GE that there will not be more
            scores coming to the specified seats, defaults to False
        :type seat_final_score: bool, optional
        """
        assert isinstance(seat, int), "seat must be int"
        assert (
            score is not None or scores is not None
        ), "Send either score or scores"
        assert (
            score is None or scores is None
        ), "Send either score or scores, not both"
        assert score is None or isinstance(
            score, (int, float)
        ), f"Unknown score type: {type(score)}, must be int or float"
        assert scores is None or isinstance(
            scores, (dict, list)
        ), f"Unknown scores type: {type(scores)}, must be dict or list"
        assert not (
            final_score and seat_final_score
        ), "Send either final_score or seat_final_score, not both"

        # get scores dict if needed
        if scores is None:
            scores = {seat: score}
        elif isinstance(scores, list):
            scores = {seat: score for seat, score in enumerate(scores)}

        self._send_threadsafe(
            "scoreUpdate",
            payload={
                "scores": scores,
                "endGame": final_score,
                "seatEndGame": seat_final_score,
            },
        )

    def send_state_alive(self, seat=0):
        """Send a state update: alive to the game engine

        :param seat: seat number, defaults to 0
        :type seat: int, optional
        """
        assert isinstance(seat, int), "seat must be int"
        self._send_threadsafe(
            "botHealthState", seat=seat, payload={"state": "alive"}
        )

    def send_state_dead(self, seat=0):
        """Send a state update: dead to the game engine

        :param seat: seat number, defaults to 0
        :type seat: int, optional
        """
        assert isinstance(seat, int), "seat must be int"
        self._send_threadsafe(
            "botHealthState", seat=seat, payload={"state": "dead"}
        )

    def send_state_unknown(self, seat=0):
        """Send a state update: unknown to the game engine

        :param seat: seat number, defaults to 0
        :type seat: int, optional
        """
        assert isinstance(seat, int), "seat must be int"
        self._send_threadsafe(
            "botHealthState", seat=seat, payload={"state": "unknown"}
        )

    def send_pre_game_ready(self, seat=0):
        """Tell the GE that a seat is ready to finish on_pre_game

        :param seat: seat number, defaults to 0
        :type seat: int, optional
        """
        assert isinstance(seat, int), "seat must be int"
        self._send_threadsafe("preGameReady", seat=seat, payload={"val": True})

    def send_pre_game_not_ready(self, seat=0):
        """Tell the GE that a seat is not ready to finish on_pre_game

        :param seat: seat number, defaults to 0
        :type seat: int, optional
        """
        assert isinstance(seat, int), "seat must be int"
        self._send_threadsafe(
            "preGameReady", seat=seat, payload={"val": False}
        )

    def set_current_seat(self, seat):
        """Tell GE the currently playing seat

        :param seat: current player seat
        :type seat: int
        """
        assert isinstance(seat, int), "seat must be int"
        self._send_threadsafe("setCurrentPlayer", seat=seat)

    def send_playing_ended(self):
        """Tell the GE that the Game is ready to move to on_finish
        """
        self._send_threadsafe("playingEnded")

    def log_admin(self, message, also_log=False):
        self._send_threadsafe("adminLog", payload={"message": message})
        if also_log:
            logging.info(message)

    def _send_threadsafe(
        self, event, src=None, seat=0, payload={}, callback=None
    ):
        """Send message to GE, not to be used directly

        :param event: Event name
        :type event: String
        :param payload: Message payload, defaults to {}
        :type payload: dict, optional
        :param callback: Message acknowledgement callback function,
            defaults to None
        :type payload: function/None, optional
        """
        self._socket_handler.send_socketio_threadsafe(
            event,
            "gameEngine",
            seat,
            src=src,
            payload=payload,
            callback=callback,
        )

    async def _send(self, event, src=None, seat=0, payload={}, callback=None):
        """Send message to GE asyncronously, not to be used directly

        :param event: Event name
        :type event: String
        :param payload: Message payload, defaults to {}
        :type payload: dict, optional
        :param callback: Message acknowledgement callback function,
            defaults to None
        :type payload: function/None, optional
        """
        await self._socket_handler.send_socketio(
            event,
            "gameEngine",
            seat,
            src=src,
            payload=payload,
            callback=callback,
        )
