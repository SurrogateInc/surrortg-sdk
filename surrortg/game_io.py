import logging
from enum import Enum

from .config_parser import get_config
from .network.message_router import MultiSeatMessageRouter
from .network.socket_handler import SocketHandler

SURRORTG_VERSION = "0.2.2"


class ConfigType(Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"


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
        device_id,
    ):
        self._config = get_config(config_path)

        if device_id is not None:
            self._config["device_id"] = device_id
        self.device_id = self._config["device_id"]
        self.input_bindings = {}
        self._custom_configs = []
        self._message_router = MultiSeatMessageRouter(robot_log_handler)

        # If type is not string (deprecated old interface), assume type is
        # RobotType. Not testing it directly because of circlar imports
        if type(robot_type) is not str:
            robot_type = robot_type.value

        self._socket_handler = SocketHandler(
            self._config["game_engine"]["url"],
            query={
                "clientType": "robot",
                "robotType": robot_type,
                "robotVersion": SURRORTG_VERSION,
                "clientId": self._config["device_id"],
                "gameId": self._config["game_engine"]["id"],
                "token": self._config["game_engine"]["token"],
            },
            message_callbacks=[
                ge_message_handler,
                self._message_router.handle_message,
            ],
            response_callbacks={self._is_config_message: ge_message_handler},
            socketio_connect_callback=self._send_controller_ready,
            socketio_logging_level=socketio_logging_level,
        )
        self._can_register_inputs = False

    def _is_config_message(self, message):
        return message.src == "gameEngine" and message.event == "config"

    def _get_inputs(self):
        bindings = []
        for command_id, obj in self.input_bindings.items():
            bindings.append({"commandId": command_id, **obj})
        return bindings

    def register_config(
        self,
        name,
        value_type,
        default,
        is_robot_specific,
        minimum=None,
        maximum=None,
    ):
        """Registers custom configs

        Registers a custom config variable which can be edited through the
        game's settings page in surrogate.tv
        The config can either be specific for the robot or a game-wide setting.
        Config names must be unique, and configs can only be registered during
        on_init stage of the game loop.

        :param name: Name of the config
        :type name: string
        :param value_type: Type of the variable
        :type value_type: ConfigType or
            "boolean" | "string" | "number" | "integer"
        :param default: Initial default value for the variable
        :type default: Must be of the value_type, e.g. if value_type is string
            this must be string as well.
        :param is_robot_specific: True if the config variable is for this robot
            only, False if this is game-wide variable
        :type is_robot_specific: boolean
        :param minimum: Optional minimum value for numeric configs
        :type minimum: Number if value_type is number, int if value_type is
            integer. Otherwise this must be None
        :param maximum: Optional maximum value for numeric configs
        :type maximum: Number if value_type is number, int if value_type is
            integer. Otherwise this must be None
        """
        if not self._can_register_inputs:
            raise RuntimeError("register_config called outside on_init")

        assert isinstance(name, str), "'name' must be a string"
        assert isinstance(
            value_type, ConfigType
        ), "'value_type' must be a valid ConfigType (string | number | bool)"
        if type(value_type) is not str:
            value_type = value_type.value
        assert isinstance(
            is_robot_specific, bool
        ), "'is_robot_specific' must be a boolean"
        if value_type == "string":
            assert isinstance(
                default, str
            ), "'default' must be a string if ConfigType.STRING"
            assert (
                minimum is None and maximum is None
            ), "String config cannot have min/max value"
        elif value_type == "number":
            assert isinstance(
                default, (int, float)
            ), "'default' must be a number if ConfigType.NUMBER"
            for val in [minimum, maximum]:
                assert val is None or isinstance(
                    val, (int, float)
                ), "min/max val has to be float, int or None"
        elif value_type == "integer":
            assert isinstance(
                default, int
            ), "'default' must be an integer if ConfigType.NUMBER"
            for val in [minimum, maximum]:
                assert val is None or isinstance(val, int)
                "min/max val has to be float, int or None"
        elif value_type == "boolean":
            assert isinstance(
                default, bool
            ), "'default' must be a boolean if ConfigType.BOOLEAN"

        if value_type in ["integer", "number"]:
            if minimum is not None:
                assert default >= minimum, "'default' must be at least minimum"
            if maximum is not None:
                assert default <= maximum, "'default' must be at most maximum"

        self._custom_configs.append(
            {
                "name": name,
                "valueType": value_type,
                "isRobotSpecific": is_robot_specific,
                "default": default,
                "minimum": minimum,
                "maximum": maximum,
            }
        )

    def register_inputs(self, inputs, admin=False, bindable=True):
        """Registers inputs

        Input names must be unique.
        If the same input name already exists, error is risen.
        The inputs can be registered only during on_init.

        :param inputs: A dictionary of input device names and objects.
        :type inputs: dict{String: Input}
        :param admin: Describes if the input is for admin use only,
            defaults to False
        :type admin: bool, optional
        :param bindable: Describes if the input can be bound to user
            input. Defaults to True.
        :raises RuntimeError: if input names are not unique
        :raises RuntimeError: if called outside on_init
        """
        if not self._can_register_inputs:
            raise RuntimeError("register_inputs called outside on_init")

        for input_id, handler_obj in inputs.items():
            if input_id in self.input_bindings:
                raise RuntimeError(f"Duplicate input_ids: {input_id}")
            self._message_router.register_input(input_id, handler_obj, admin)
            if bindable:
                self.input_bindings[input_id] = {
                    "type": handler_obj.get_name(),
                    "admin": admin,
                    **handler_obj._get_default_keybinds(),
                }

    def enable_inputs(self):
        """Enable all registered inputs"""
        self._message_router.set_enabled_all(True)

    def disable_inputs(self):
        """Disable all registered inputs"""
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
        # return if seat is not specified or not found
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
        :param seat: seat number, used only with a single score, defaults to 0
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
        """Tell the GE that the Game is ready to move to on_finish"""
        self._send_threadsafe("playingEnded")

    def log_admin(self, message, also_log=False):
        self._send_threadsafe("adminLog", payload={"message": message})
        if also_log:
            logging.info(message)

    def _send_controller_ready(self):
        msg = {"inputs": self._get_inputs(), "configs": self._custom_configs}
        logging.info(f"Sending controller ready: {msg}")
        self._send_threadsafe("controllerReady", payload=msg)

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
        """Send message to GE asynchronously, not to be used directly

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
