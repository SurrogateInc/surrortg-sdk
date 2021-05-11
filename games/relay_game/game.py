import logging

from games.relay_game.config import ON_LEVEL_LOW, RELAY_SWITCHES
from surrortg import Game
from surrortg.devices import Relay
from surrortg.inputs import Switch


class RelaySwitch(Switch):
    def __init__(self, pin, input_name, on_level_low):
        self.input_name = input_name
        self.relay = Relay(pin, on_level_low)

    async def on(self, seat=0):
        self.relay.on()
        logging.info(f"{self.input_name} pressed.")

    async def off(self, seat=0):
        self.relay.off()
        logging.info(f"{self.input_name} released.")

    async def shutdown(self, seat=0):
        self.relay.stop()


class RelayGame(Game):
    async def on_init(self):
        # Register player inputs
        for input_name, pin_number in RELAY_SWITCHES.items():
            self.io.register_inputs(
                {input_name: RelaySwitch(pin_number, input_name, ON_LEVEL_LOW)}
            )


if __name__ == "__main__":
    # Start running the game
    RelayGame().run()
