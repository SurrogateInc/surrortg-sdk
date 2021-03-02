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

    async def handle_config(  # noqa: C901
        self, ge_config, local_bot_config={},
    ):
        """Handle robot configuration

        :param ge_config: Configuration from the game engine
        :type ge_config: dict
        :param local_bot_config: Local configuration for bots that maps seats
            to bot addresses, defaults to an empty dict
        :type local_bot_config: dict, optional
        :return: Current set and bots in current set, mapped by seats
        :rtype: (int, dict)
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
            self.current_set = await self.select_set()
            logging.info("Reading current set from file")

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
                try:
                    addr = bot_data["custom"]["address"]
                except KeyError:
                    logging.error(
                        f"Failed to parse address for seat {seat}. "
                        f"Is your local bot config correct?"
                    )
                    continue

            if (
                seat in self.bots
                and addr != self.bots[seat]["custom"]["address"]
            ):
                logging.info(
                    f"Duplicate seat {seat} reassigned from "
                    f"{self.bots[seat]['custom']['address']} to {addr}"
                )

            endpoint = await open_remote_endpoint(addr, BOT_UDP_PORT)
            self.endpoints[seat] = endpoint
            self.bots[seat] = bot_data

            if "custom" in self.bots[seat]:
                self.bots[seat]["custom"]["address"] = addr
            else:
                self.bots[seat]["custom"] = {"address": addr}

        for input_impl in self.inputs.values():
            input_impl.set_endpoints(self.endpoints)

        logging.info(
            f"UdpBot config done for {len(self.bots)}/{len(ge_bot_config)} "
            f"bots, using set {self.current_set}"
        )
        if len(self.bots) < len(ge_bot_config):
            logging.warning(
                f"Config for {len(ge_bot_config)} bots received from GE, "
                f"but only {len(self.bots)} could be configured. "
                f"Make sure there are no duplicate seats in admin page"
            )
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
            logging.warning(
                f"Set file not found from {set_file_name}! "
                f"Defaulting set to 0"
            )
            set_num = 0
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
