import logging

from surrortg import Game
from surrortg.inputs import Joystick


class MyJoystick(Joystick):
    async def handle_coordinates(self, x, y, seat=0):
        logging.info(f"\tx:{x}, y:{y}")

    async def reset(self, seat=0):
        logging.info("reset")


class MyGame(Game):
    async def on_init(self):
        self.io.register_inputs({"joystick_main": MyJoystick()})


MyGame().run()
