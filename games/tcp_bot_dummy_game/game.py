import logging

from surrortg import Game
from surrortg.devices.tcp import TcpBot, TcpCommandId, TcpSwitch


class TcpTestBot(TcpBot):
    """Class for TCP-controlled bots with a switch

    Inputs include a switch
    """

    def __init__(self, game_io):
        super().__init__(game_io)
        self._switch = TcpSwitch(TcpCommandId.CUSTOM_1)
        self.add_inputs({"switch": self._switch})


class TcpBotDummyGame(Game):
    async def on_init(self):
        # Create the TCP bots
        self.bot = TcpTestBot(self.io)
        # Register inputs
        self.io.register_inputs(self.bot.inputs)

    async def on_config(self):
        set_num = await self.bot.handle_config(
            self.configs,
            bot_listener_cb=self.receive_tcp_cb,
        )
        return set_num

    async def receive_tcp_cb(self, seat, cmd_id, cmd_val):
        logging.info(f"Response from seat {seat}, cmd {cmd_id}: {cmd_val}")

    async def on_start(self):
        pass
        # add game logic here

    async def on_exit(self, reason, exception):
        # Shutdown tcp bot
        await self.bot.shutdown()


if __name__ == "__main__":
    TcpBotDummyGame().run()
