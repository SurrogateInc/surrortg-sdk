import asyncio
import logging
import struct

from surrortg import ConfigType

from .tcp_protocol import open_tcp_endpoint

BOT_TCP_PORT = 31338
CONFIG_IP_ADDR_NAME = "microcontroller_ip_addr"
set_file_name = "/var/lib/srtg/current_set"


class TcpBot:
    """Base class for all bots that are controlled with TCP commands

    :param game_io: The game's GameIO object
    :type game_io: GameIO
    """

    def __init__(self, game_io):
        self.inputs = {}
        self.bots = {}
        self.endpoints = {}
        self.bot_listener_tasks = {}
        self.current_set = 0
        self._loop = asyncio.get_running_loop()
        self.game_io = game_io
        self.game_io.register_config(
            CONFIG_IP_ADDR_NAME, ConfigType.STRING, "xxx.xxx.xxx.xxx", True
        )

    async def handle_config(  # noqa: C901
        self,
        ge_config,
        local_bot_config={},
        bot_listener_cb=None,
    ):
        """Handle robot configuration

        :param ge_config: Configuration from the game engine
        :type ge_config: dict
        :param local_bot_config: Local configuration for bots that maps seats
            to bot addresses, defaults to an empty dict
        :type local_bot_config: dict, optional
        :param bot_listener_cb: This is executed when udp message is received
            from a bot, defaults to None. Must take seat, cmd_id and cmd_val
            as parameters.
        :type bot_listener_cb: function, optional
        :return: Current set
        :rtype: int
        """
        await self.shutdown()
        set_reading_succeeded = False

        try:
            ge_bot_config = ge_config["robots"]
        except KeyError:
            logging.warning("Failed to parse robot configs")
            return (0, {})

        if "currentSet" in ge_config:
            try:
                self.current_set = int(ge_config["currentSet"])
                set_reading_succeeded = True
            except ValueError:
                logging.warning("Failed to cast current set number to int")

        if not set_reading_succeeded:
            logging.info("Reading current set from file")
            self.current_set = await self.select_set()

        self.bots = {}
        self.endpoints = {}

        for bot_data in ge_bot_config:
            addr = None
            try:
                seat = int(bot_data["seat"])
            except (KeyError, ValueError):
                logging.error("Failed to parse seat for one of the robots")
                continue

            # Override GE bot configs with local ones, if found
            if seat in local_bot_config:
                addr = local_bot_config[seat]
            else:
                if "custom" in bot_data:
                    if "address" in bot_data["custom"]:
                        addr = bot_data["custom"]["address"]
                    elif CONFIG_IP_ADDR_NAME in bot_data["custom"]:
                        addr = bot_data["custom"][CONFIG_IP_ADDR_NAME]
                    else:
                        logging.error(
                            f"Failed to parse address for seat {seat}"
                        )
                else:
                    logging.error(
                        f"Failed to parse address for seat {seat}! "
                        "'custom' field not in config for that seat"
                    )
                    continue

            if seat in self.bots:
                logging.info(
                    f"Duplicate seat {seat} found from configs, "
                    f"using address {addr}."
                )

            endpoint = await open_tcp_endpoint(addr, BOT_TCP_PORT)

            if endpoint is None:
                logging.error(
                    f"Connection failed to seat {seat}, {addr}:{BOT_TCP_PORT}"
                )
                continue

            self.endpoints[seat] = endpoint
            self.bots[seat] = bot_data

        # Register listener tasks for all endpoints if callback is given
        if bot_listener_cb is not None:
            for seat in self.endpoints:
                self.bot_listener_tasks[seat] = asyncio.create_task(
                    self._receive_messages_from_seat(seat, bot_listener_cb)
                )

        for input_impl in self.inputs.values():
            input_impl.set_endpoints(self.endpoints)

        logging.info(
            f"TcpBot config done for {len(self.bots)}/{len(ge_bot_config)} "
            f"bots, using set {self.current_set}"
        )
        if len(self.bots) < len(ge_bot_config):
            logging.warning(
                f"Config for {len(ge_bot_config)} bots received from GE, "
                f"but only {len(self.bots)} could be configured"
            )
        return self.current_set

    def get_bots_in_current_set(self):
        """Returns all the configured bots of the currently selected set

        :return: Successfully configured robots in the currently selected set
            and their information as received from the Game Engine
        :rtype: dict
        """
        return dict(
            filter(
                lambda elem: (
                    self.bots[elem[0]]["set"] == self.current_set
                    and self.bots[elem[0]]["enabled"]
                ),
                self.bots.items(),
            )
        )

    async def select_set(self):
        """Reads the set from the set file and returns it

        :return: Newly selected set number
        :rtype: int
        """
        try:
            with open(set_file_name, "r") as f:
                set_num = int(f.read())
        except FileNotFoundError:
            logging.warning(
                f"Set file not found from {set_file_name}! "
                f"Defaulting set to 0"
            )
            set_num = 0
        except ValueError:
            logging.warning("Failed to cast set number from file to int")
            raise

        return set_num

    def add_inputs(self, new_inputs):
        """Appends the given inputs to the bot's input configuration

        Does not override previous configurations

        :param new_input: Inputs to append to the existing ones
        :type new_input: dict
        """
        self.inputs.update(new_inputs)

    async def shutdown(self):
        """Resets all registered inputs for all bots

        Also cancels registered bot listener tasks
        and closes all endpoints
        """
        for listener_task in self.bot_listener_tasks.values():
            listener_task.cancel()

        for seat, endpoint in self.endpoints.items():
            for input_impl in self.inputs.values():
                logging.info(f"Shutting down input for seat {seat}")
                await input_impl.shutdown(seat)
            await endpoint.close()

    async def _receive_messages_from_seat(self, seat, on_receive_cb):
        """Receives tcp messages from specific bot

        :param seat: Robot seat
        :type seat: int
        :param on_receive_cb: Function to call when message is received,
            must take seat, cmd_id and cmd_val as parameters
        :type on_receive_cb: function
        """
        logging.info(f"Receiving messages for seat {seat}")
        endpoint = self.endpoints[seat]
        try:
            while True:
                data = await endpoint.receive_exactly(2)
                cmd_id, cmd_val = struct.unpack("BB", data)
                await on_receive_cb(seat, cmd_id, cmd_val)
        except asyncio.CancelledError:
            logging.info(f"Message receiver for seat {seat} cancelled")
        except ConnectionResetError:
            logging.error(f"Message receiver for seat {seat} stopped")
