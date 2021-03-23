import logging

import pigpio

from games.relay_game.config import GPIO_SWITCHES, ON_LEVEL
from surrortg import Game
from surrortg.inputs import Switch


class GPIOSwitch(Switch):
    def __init__(self, pi, pin, input_name):
        self._pi = pi
        self.pin = pin
        self.input_name = input_name

        # Set GPIO pin levels according to the configuration
        if ON_LEVEL == "HIGH":
            self.on_level = pigpio.HIGH
            self.off_level = pigpio.LOW
        else:
            self.on_level = pigpio.LOW
            self.off_level = pigpio.HIGH

        # Initialize output pin
        self._pi.set_mode(self.pin, pigpio.OUTPUT)
        self._pi.write(self.pin, self.off_level)

    async def on(self, seat=0):
        self._pi.write(self.pin, self.on_level)
        logging.info(f"{self.input_name} pressed.")

    async def off(self, seat=0):
        self._pi.write(self.pin, self.off_level)
        logging.info(f"{self.input_name} released.")

    async def shutdown(self, seat=0):
        # Set pin to input mode to make it safe
        self._pi.set_pull_up_down(self.pin, pigpio.PUD_OFF)
        self._pi.set_mode(self.pin, pigpio.INPUT)


class RelayGame(Game):
    async def on_init(self):
        # Connect to pigpio daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon.")

        # Register player inputs
        for input_name, pin_number in GPIO_SWITCHES.items():
            self.io.register_inputs(
                {input_name: GPIOSwitch(self.pi, pin_number, input_name)}
            )


if __name__ == "__main__":
    # Start running the game
    RelayGame().run()
