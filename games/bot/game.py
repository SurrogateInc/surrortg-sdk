import logging

from gpiozero import Robot

from surrortg import Game
from surrortg.inputs import Directions, Joystick


class Bot(Joystick):
    def __init__(self):
        # Create new bot with the correct pins
        self.robot = Robot(left=(17, 27), right=(18, 22))

    async def handle_coordinates(self, x, y, seat=0):
        # Parse direction out of coordinates
        direction = self.get_direction_8(x, y)

        # log the input
        logging.info(f"Direction: {direction}")

        # Drive the bot to the direction
        if direction == Directions.TOP:
            self.robot.forward()
        elif direction == Directions.BOTTOM:
            self.robot.backward()
        elif direction == Directions.RIGHT:
            self.robot.right()
        elif direction == Directions.LEFT:
            self.robot.left()
        elif direction == Directions.MIDDLE:
            self.robot.stop()
        elif direction == Directions.TOP_RIGHT:
            self.robot.forward(curve_right=1)
        elif direction == Directions.TOP_LEFT:
            self.robot.forward(curve_left=1)
        elif direction == Directions.BOTTOM_RIGHT:
            self.robot.backward(curve_right=1)
        elif direction == Directions.BOTTOM_LEFT:
            self.robot.backward(curve_left=1)

    async def reset(self, seat=0):
        # Stop between games
        self.robot.stop()


class BotGame(Game):
    async def on_init(self):
        # Create a new bot and initialize it as input.
        # The Bot class behaves as a Joystick.
        self.io.register_inputs({"joystick_main": Bot()})


if __name__ == "__main__":
    BotGame().run()
