import asyncio
import logging

from .udp_protocol import open_remote_endpoint

BOT_UDP_PORT = 31337
set_file_name = "/var/lib/srtg/current_set"


class UdpBot:
    """Base class for all bots that are controlled with udp commands"""

    def __init__(self):
        self.inputs = {}
        self.bots = {}
        self.endpoints = {}
        self.current_set = 0
        self._loop = asyncio.get_running_loop()

    async def handle_config(self, config):
        """Handle robot configuration

        :param config: Configuration from game engine
        :type config: dict
        :return: Current set and bots in current set, mapped by seats
        :rtype: (int, dict)
        """
        await self.shutdown()
        set_reading_succeeded = False

        try:
            bot_config = config["robots"]
        except KeyError:
            logging.warning("Failed to parse robot configs")
            return (0, {})

        if "currentSet" in config:
            try:
                self.current_set = int(config["currentSet"])
                set_reading_succeeded = True
            except ValueError:
                logging.warning("Failed to cast current set number to int")

        if not set_reading_succeeded:
            self.current_set = await self.select_set()
            logging.info("Reading current set from file")

        self.bots = {}
        self.endpoints = {}
        for bot in bot_config:
            try:
                seat = int(bot["seat"])
                addr = bot["custom"]["address"]
            except (KeyError, ValueError):
                logging.error("Failed to parse one of the robots' info")
                continue

            if (
                seat in self.bots
                and addr != self.bots[seat]["custom"]["address"]
            ):
                logging.info(
                    f"Seat {seat} reassigned from "
                    f"{self.bots[seat]['custom']['address']} to {addr}"
                )

            endpoint = await open_remote_endpoint(addr, BOT_UDP_PORT)
            self.endpoints[seat] = endpoint
            self.bots[seat] = bot

        for input_impl in self.inputs.values():
            input_impl.set_endpoints(self.endpoints)
        logging.info(f"UdpBot config done, set {self.current_set} in use")
        return (self.current_set, self.get_bots_in_current_set())

    def get_bots_in_current_set(self):
        """Returns all the enabled bots of the currently selected set

        :return: Enabled robots in the currently selected set
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
            logging.warning("Set file not found!\n")
            raise
        except ValueError:
            logging.warning("Failed to cast set number from file to int")
            raise

        return set_num

    def add_input(self, new_input):
        """Appends the given input to the bot's input configuration

        Does not override previous configurations

        :param new_input: Input to append to the existing ones
        :type new_input: dict
        """
        self.inputs.update(new_input)

    async def shutdown(self):
        """Resets all registered inputs for all bots,
        and then closes all endpoints
        """

        for seat, endpoint in self.endpoints.items():
            for input_impl in self.inputs.values():
                asyncio.run_coroutine_threadsafe(
                    input_impl.shutdown(seat), self._loop
                )
            endpoint.close()
