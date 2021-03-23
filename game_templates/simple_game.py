import asyncio
import logging
import time

from surrortg import Game  # First we need import the Game
from surrortg.inputs import Switch  # and our preferred input(s)
from surrortg.inputs import Joystick


# Create a custom switch, it really can do what ever you want.
class MySwitch(Switch):
    async def on(self, seat=0):
        # FIRE!!! or jump or drive or whatever you want
        logging.info(f"on for seat {seat}")

    async def off(self, seat=0):
        # stop the thing you were doing
        logging.info(f"off for seat {seat}")


# Create a joystick, it can control anything with 4 or 8 directions
class MyJoystick(Joystick):
    async def handle_coordinates(self, x, y, seat=0):
        logging.info(f"\tx:{x}, y:{y}")
        logging.info(f"{self.get_direction_8(x,y)}")
        # handle player input here

    async def reset(self, seat=0):
        logging.info("reset")


class SimpleGame(Game):
    async def on_init(self):
        # During the Game initialization callback register your switch so the
        # Game Engine knows where to send the user input during the games.
        # Make sure that the name matches with the admin panel one.
        self.io.register_inputs({"switch": MySwitch()})
        self.io.register_inputs({"joystick_main": MyJoystick()})

    async def on_start(self):
        """
        Simple game simulates a 3 player game where timestamp scores
        are sent for each seat and the game is ended with the final score
        parameter in the third send score method.
        """
        start_time = time.time()
        await asyncio.sleep(5)
        score_temp = self.convert_to_ms(time.time() - start_time)
        self.io.send_score(score=score_temp, seat=0)
        await asyncio.sleep(5)
        score_temp = self.convert_to_ms(time.time() - start_time)
        self.io.send_score(score=score_temp, seat=1)
        await asyncio.sleep(5)
        score_temp = self.convert_to_ms(time.time() - start_time)
        self.io.send_score(score=score_temp, seat=2, final_score=True)

    def convert_to_ms(self, time):
        """
        When a game is using timestamp scores, the controller must provide the
        scores as milliseconds. This is a simple conversion function that
        converts seconds to milliseconds.

        :param time: Time in seconds
        :returns: Time in milliseconds
        """
        text = f"{time:.2}"
        converted = float(text)
        scaled = converted * 1000
        return scaled


# And now you are ready to play!
if __name__ == "__main__":
    SimpleGame().run()

# More info about:
# Game: https://docs.surrogate.tv/modules/surrortg.html#module-surrortg.game # noqa: E501
# Switch: https://docs.surrogate.tv/modules/surrortg.inputs.html#surrortg.inputs.switch.Switch # noqa: E501
# Inputs: https://docs.surrogate.tv/modules/surrortg.inputs.html
# More examples and the full documentation: https://docs.surrogate.tv/game_development.html # noqa: E501
