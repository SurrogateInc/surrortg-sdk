import logging

from games.roomba_driver.config import ON_LEVEL_LOW, PINS
from surrortg import Game
from surrortg.devices import Relay
from surrortg.inputs import Switch


class RelaySwitch(Switch):
    def __init__(self, pin, on_level_low):
        self.relay = Relay(pin, on_level_low)
        self.pin = pin

    async def on(self, seat=0):
        logging.info(f"Relay {self.pin} on")
        self.relay.on()

    async def off(self, seat=0):
        logging.info(f"Relay {self.pin} off")
        self.relay.off()


class RoombaDriverGame(Game):
    async def on_init(self):
        # Initialize input
        self.inputs = {}
        for key, pin in PINS.items():
            switch = RelaySwitch(pin, ON_LEVEL_LOW)
            self.inputs[key] = switch

        # Register input
        self.io.register_inputs(self.inputs)

    async def on_start(self):
        logging.info("Game starts")

    async def on_finish(self):
        logging.info("Game ends")
        self.io.send_score(score=1)


if __name__ == "__main__":
    # Start running the game
    RoombaDriverGame().run()
