import asyncio
import functools
import logging
from enum import Enum
from signal import SIGINT, SIGTERM, SIGUSR1

from .game_io import GameIO

# Reason codes are passed to the user as an on_exit parameter.
# Code and description is also logged.
EXIT_REASONS = {
    -1: "Unknown exit reason",
    0: "Uncaught exception",
    1: "Interrupted (SIGINT)",
    2: "Terminated (SIGTERM)",
    3: "Update (SIGUSR1)",
}

# Custom implementation of these methods is checked at the start of run().
# If not found, it this will be logged: name + DEFAULT_INFO + ADDITIONAl_INFO.
CHECK_IMPLEMENTATION = [
    "on_init",
    "on_config",
    "on_prepare",
    "on_pre_game",
    "on_countdown",
    "on_start",
    "on_finish",
    "on_exit",
]
NOT_IMPLEMENTED_DEFAULT_INFO = "not implemented."
NOT_IMPLEMENTED_ADDITIONAL_INFO = {
    "on_init": " No inputs/outputs were registered.",
    "on_config": " Using the current set.",
}

# Mapping from GE event to Game loop event names and handler names
# This is used for logging and starting the correct event handler
GE_EVENT_TO_NAME_AND_HANDLER = {
    "config": ("on_config", "_on_config_handler"),
    "prepareGame": ("on_prepare", "_on_prepare_handler"),
    "preGameStarted": ("on_pre_game", "_on_pre_game_handler"),
    "countdownStarted": ("on_countdown", "_on_countdown_handler"),
    "gameStarted": ("on_start", "_on_start_handler"),
    "gracePeriodStarted": ("on_finish", "_on_finish_handler"),
    "gameEnded": ("game_ended", "_on_end_handler"),
}

# logging from GE
ROBOT_LOG_METHODS = {
    "critical": logging.critical,
    "error": logging.error,
    "warning": logging.warning,
    "info": logging.info,
    "debug": logging.debug,
}

# custom Game messages to GE:
APPROVE_START = "robotApproveStart"


class RobotType(Enum):
    ROBOT = "robot"
    LOGICAL = "logical"


class Game:
    """A basis for all games on the Surrogate.tv platform

    Game consists of callback methods, which are automatically called
    by the game engine during the game loop. All messaging with the game
    engine is done through GameIO class, which is accessed through self.io.
    The game loop is started with a run() call.

    The players and admin panel configurations can be accessed through
    self.players and self.configs properties.
    """

    @property
    def io(self):
        """Access to the GameIO object

        GameIO is used for communication with the game engine.

        :raises RuntimeError: when accessed before run()
        :return: GameIO object instance
        :rtype: GameIO
        """
        if self._run_not_called():
            raise RuntimeError("self.io accessed before calling run()")
        return self._io

    @property
    def configs(self):
        """:param configs: A dictionary of admin panel configurations

        Configs are available everywhere except during on_init.

        :raises RuntimeError: when accessed before run() or during on_init
        :rtype: dict
        """
        if self._run_not_called():
            raise RuntimeError("self.configs accessed before calling run()")
        elif self._configs is None:
            raise RuntimeError(
                "self.configs are not available. Are you trying to access "
                "them during on_init?"
            )
        return self._configs

    @property
    def players(self):
        """:param players: A list of player infos

        The players are available only during on_pre_game, on_countdown,
        on_start and on_finish.

        NOTE: because of the current implementation limitations, game.players
        could raise RuntimeError if preGame phase length is 0 seconds. The
        workaround is to set it for example to 2 seconds (the default is 0
        seconds). This can be changed from the game's Dashboard at
        www.surrogate.tv/game/<SHORT_ID>/settings > Settings > Game Engine.

        :raises RuntimeError: when accessed before run() or if not available
        :rtype: list[dict]
        """
        if self._run_not_called():
            raise RuntimeError("self.players accessed before calling run()")
        elif self._players is None:
            raise RuntimeError(
                "self.players are not available. Are you trying to access "
                "them before they are available? The players are available "
                "only during on_pre_game, on_countdown, on_start and "
                "on_finish."
            )
        return self._players

    def run(
        self,
        config_path=None,
        logging_level=logging.INFO,
        socketio_logging_level=logging.WARNING,
        start_games_inputs_enabled=True,
        robot_type=RobotType.ROBOT,
        device_id=None,
    ):
        """Connect to the game engine and start the Game loop

        :param config_path: custom configuration file path, defaults to None
        :type config_path: str/None, optional
        :param logging_level: logging level, defaults to logging.INFO
        :type logging_level: int/None, optional
        :param socketio_logging_level: SocketIO logging level, defaults to
            logging.WARNING
        :type socketio_logging_level: Int, optional
        :param start_games_inputs_enabled: Decides whether the inputs are
            automatically enabled at the start of on_start method, defaults
            to True
        :type start_games_inputs_enabled: bool, optional
        :param robot_type: Decides whether the python unit is a controllable
            robot unit, or a logical unit. Defaults to "robot", for logical,
            use "logical". Logical robot type is for advanced use only.
        :type robot_type: RobotType, optional
        :param device_id: Overrides device_id from config file. Note: config
            file device_id is mandatory field even when this parameter is used
        :type device_id: str/None, optional
        """

        if logging_level is not None:
            logging.basicConfig(
                format=(
                    "surrortg-{levelname}: {message:<40} ({filename}:{lineno})"
                ),
                style="{",
                level=logging_level,
            )
        self.start_games_inputs_enabled = start_games_inputs_enabled

        # this structure makes testing easier
        self._pre_run(
            config_path, socketio_logging_level, robot_type, device_id
        )
        self._run()
        self._post_run()

    async def on_init(self):
        """Initialize the game before connecting to the game engine

        The input devices are registered here with
        a self.io.register_inputs({...}) call.
        """
        pass

    async def on_config(self):
        """Do things before the game engine starts fetching new players

        For example new inputs can be registered here if they change
        based on self.configs.
        """
        pass

    async def on_prepare(self):
        """Do some preparations before the players connect"""
        pass

    async def on_pre_game(self):
        """Do some preparations after the players connect

        The game won't start before every robot has called
        self.io.send_pre_game_ready(), or maximum pre game time is reached.
        If the player inputs are needed here, they can be enabled with
        self.io.enable_inputs() call. On default all inputs are disabled here.

        The return value of this method will set as the self._current_seat
        value (which is an integer).
        """
        pass

    async def on_countdown(self):
        """Do things during the game countdown"""
        pass

    async def on_start(self):
        """Inputs are now enabled. Scores, laps and progress are counted.

        self._current_seat is set to 0 by default, if it has not been set in
        on_pre_game().

        The game engine will choose the winner based on the game type set on
        the admin panel. self.io.send_playing_ended() call can be used to
        signal the game engine that some seat has finished.
        """
        pass

    async def on_finish(self):
        """Do something when the robot finishes the game

        The game is finished for example when someone has enough score or
        laps or when the time is up. These rules can be set from the admin
        panel.
        """
        pass

    async def on_exit(self, reason, exception):
        """This method is called just before the program exits

        The exit reason code and exception are passed as parameters.

        Exit reasons:

        +------+---------------------+
        | Code | Reason              |
        +======+=====================+
        |-1    | Unknown exit reason |
        +------+---------------------+
        | 0    | Uncaught exception  |
        +------+---------------------+
        | 1    | Interrupted (SIGINT)|
        +------+---------------------+
        | 2    | Terminated (SIGTERM)|
        +------+---------------------+
        | 3    | Update (SIGUSR1)    |
        +------+---------------------+

        :param reason: Reason code of the program exit.
        :type reason: int
        :param exception: Exception that caused the exit
        :type exception: Exception/None
        """
        pass

    def _run_not_called(self):
        return not hasattr(self, "_io")

    def _pre_run(
        self, config_path, socketio_logging_level, robot_type, device_id
    ):
        # log info if certain methods not implemented
        for method_name in CHECK_IMPLEMENTATION:
            if self._not_implemented(method_name):
                logging.debug(self._get_not_implemented_message(method_name))

        # GameIO should only be accessed through property self.io
        self._io = GameIO(
            self._handle_ge_message,
            self._handle_robot_log,
            config_path,
            socketio_logging_level,
            robot_type,
            device_id,
        )

        # set flag for updates between games
        self._update_requested = False

        # init ge message handling
        self._current_ge_task = None
        self._configs = None
        self._players = None
        self._current_seat = None
        self._on_finish_started = False

        # set initial exit_reason, this should be different
        # when the program ends
        self._exit_reason = -1
        self._exception = None

    def _not_implemented(self, method_name):
        return getattr(type(self), method_name) == getattr(Game, method_name)

    def _get_not_implemented_message(self, method_name):
        return (
            f"{method_name} {NOT_IMPLEMENTED_DEFAULT_INFO}"
            f"{NOT_IMPLEMENTED_ADDITIONAL_INFO.get(method_name, '')}"
        )

    def _run(self):
        asyncio.run(self._main())

    def _post_run(self):
        # get still existing tasks
        tasks = asyncio.all_tasks(loop=self._loop)
        if len(tasks) > 0:
            logging.info(
                f"{len(tasks)} asyncio tasks running on Game loop, "
                "sending cancel"
            )
            # cancel existing tasks
            for task in tasks:
                task.cancel()

            # wait for the tasks to end
            self._loop.run_until_complete(asyncio.gather(*tasks))

        logging.info("Game ended.\n")

    async def _main(self):
        # get ready to handle GE messages
        self._handler_lock = asyncio.Lock()

        # Allow self.io.register_inputs usage and initialize the game.
        # Then forbid all later self.io.register_inputs calls.
        self.io._can_register_inputs = True
        await self.on_init()
        self.io._can_register_inputs = False

        # play the game until interrupted, terminated or crashed
        self._main_task = asyncio.create_task(self.io._socket_handler.run())

        # add signal handlers
        self._loop = asyncio.get_running_loop()
        self._loop.add_signal_handler(
            SIGINT, functools.partial(self._exit_signal_handler, 1)
        )
        self._loop.add_signal_handler(
            SIGTERM, functools.partial(self._exit_signal_handler, 2)
        )
        self._loop.add_signal_handler(SIGUSR1, self._request_update)

        try:
            await self._main_task
        except asyncio.CancelledError:
            # if asyncio.CancelledError --> was ended on purpose
            await self._exit_correctly()
        except Exception as e:
            # else _main_task did not end on purpose --> Python has crashed
            self._exit_reason = 0
            self._exception = e
            await self._exit_correctly()
            raise  # after exiting correctly, raise the original exception

    def _request_update(self):
        logging.info("Update request received")
        self._update_requested = True

    def _exit_signal_handler(self, exit_reason):
        self._exit_reason = exit_reason
        self._exception = None
        self._main_task.cancel()

    async def _exit_correctly(self):
        logging.info("Game ending...")
        # cancel the existing GE task if has not finished yet
        if (
            self._current_ge_task is not None
            and not self._current_ge_task.done()
        ):
            logging.info("Cancelling previous GE task due to program exit")
            self._current_ge_task.cancel()

        # log the exit reason
        logging.info(
            f"\tReason: {self._exit_reason}, {EXIT_REASONS[self._exit_reason]}"
        )
        if self._exception is not None:
            logging.info(f"\tException name: {type(self._exception).__name__}")

        # wait for on_exit to finish
        await self.on_exit(self._exit_reason, self._exception)
        await self.io.shutdown_inputs()

        # shut down connections
        await self.io._socket_handler.shutdown()

        # run() should now move to _post_run()

    async def _handle_ge_message(self, message):
        # handle only supported messages from GE
        if (
            message.src != "gameEngine"
            or message.event not in GE_EVENT_TO_NAME_AND_HANDLER
        ):
            return

        # make sure to handle only one message at a time
        async with self._handler_lock:
            # get task name and method
            task_name, handler_name = GE_EVENT_TO_NAME_AND_HANDLER[
                message.event
            ]
            method = getattr(self, handler_name)

            # cancel the current GE task if has not finished yet
            if (
                self._current_ge_task is not None
                and not self._current_ge_task.done()
            ):
                self._current_ge_task.cancel()
                try:
                    await self._current_ge_task
                except asyncio.CancelledError:
                    pass

            # create a new GE task
            self._current_ge_task = asyncio.create_task(
                self._ge_task(task_name, method, message)
            )
        try:
            # await for the new GE task to finish
            return await self._current_ge_task
        except asyncio.CancelledError:
            # if new message arrives while previous one is still being handled,
            # it will cause previous message handling to be cancelled.
            return None

    async def _ge_task(self, task_name, method, message):
        try:
            logging.info(f"'{task_name}' started")
            result = await method(message)
            logging.info(f"'{task_name}' ended")
        except asyncio.CancelledError:
            logging.info(f"'{task_name}' cancelled")
            return
        return result

    def _handle_robot_log(self, msg):
        if (
            "loggingLevel" in msg.payload
            and msg.payload["loggingLevel"] in ROBOT_LOG_METHODS.keys()
            and "message" in msg.payload
            and isinstance(msg.payload["message"], str)
        ):
            ROBOT_LOG_METHODS[msg.payload["loggingLevel"]](
                f"GE: {msg.payload['message']}"
            )
        else:
            logging.warning(f"Malformed ROBOT_LOG: {msg}")
        # TODO RD-917 add support for restarting robot from the admin panel

    def _parse_seats(self, configs):
        # Config types or structure are not enforced
        # so let's check everything before use
        seats = []
        if isinstance(configs, dict) and "robots" in configs:
            for robot in configs["robots"]:
                if isinstance(robot, dict) and "id" in robot:
                    # Leave option to remove 'robot' from
                    # the id end at some point
                    if robot["id"].endswith("robot"):
                        robot_id = robot["id"][: -len("robot")]
                    else:
                        robot_id = robot["id"]
                    if robot_id == self.io.device_id:
                        if "seat" in robot and isinstance(robot["seat"], int):
                            seats.append(robot["seat"])

        if len(seats) == 0:
            logging.warning("No seats could be parsed! Defaulting to seat 0")
            seats.append(0)

        return seats

    async def _on_config_handler(self, message):
        # end execution if update has been requested
        if self._update_requested:
            self._exit_signal_handler(3)

        # reset between games
        self._on_finish_started = False

        self._configs = self._parse_configs(message)
        self._seats = self._parse_seats(self._configs)
        set_num = await self.on_config()
        if set_num is not None:
            payload = {"set": set_num}
        else:
            payload = {}
        return payload

    async def _on_prepare_handler(self, message):
        prep_result = await self.on_prepare()
        if prep_result is None or prep_result is True:
            await self.io._send(APPROVE_START)

    async def _on_pre_game_handler(self, message):
        self._players = self._parse_players(message)
        self._current_seat = await self.on_pre_game()
        for seat in self._seats:
            self.io.send_pre_game_ready(seat=seat)

    async def _on_countdown_handler(self, message):
        await self.on_countdown()

    async def _on_start_handler(self, message):
        if self.start_games_inputs_enabled:
            self.io.enable_inputs()
        if self._current_seat is not None:
            self.io.set_current_seat(self._current_seat)
        else:
            self.io.set_current_seat(0)
        await self.on_start()

    async def _on_finish_handler(self, message):
        if not self._on_finish_started:
            self._on_finish_started = True
            await self.on_finish()

    async def _on_end_handler(self, message):
        """Called when a 'gameEnded' message is received,
        which happens after grace period ends.

        Awaits on_finish if 'gracePeriodStarted' has not been received yet,
        which is possible. This is where player inputs are disabled by
        default.
        """
        if not self._on_finish_started:
            self._on_finish_started = True
            await self.on_finish()

        self.io.disable_inputs()
        await self.io.reset_inputs()
        self._configs = None
        self._players = None

    def _parse_configs(self, message):
        return message.payload

    def _parse_players(self, message):
        return message.payload["players"]
