import argparse
import logging

from surrortg import Game
from surrortg.inputs import Joystick


class MyJoystick(Joystick):
    async def handle_coordinates(self, x, y, seat=0):
        logging.info(f"\tx:{x}, y:{y}")
        # handle player input here

    async def reset(self, seat=0):
        logging.info("reset")


class DummyGame(Game):
    async def on_init(self):
        self.io.register_inputs({"joystick_main": MyJoystick()})

    async def on_start(self):
        pass
        # add game logic here


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Dummy game")
    parser.add_argument(
        "-c",
        "--conf",
        metavar="",
        help="path to configuration .toml file",
        required=False,
    )
    args = parser.parse_args()
    if args.conf is not None:
        DummyGame().run(config_path=args.conf)
    else:
        DummyGame().run()
