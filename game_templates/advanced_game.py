from surrortg import Game  # First we need import the Game
from surrortg.inputs import Directions, Joystick  # and our preferred input(s)


# Create a custom Joystick, it really can do what ever you want.
class MyJoystick(Joystick):
    """
    Advanced game documentation
    """

    def __init__(self, io):
        self.io = io  # save io for sending updates to the game engine
        self.progress = 0.0  # initialize progress with 0.0

    # do things based on Joystick directions
    async def handle_coordinates(self, x, y, seat=0):
        direction = self.get_direction_4(x, y)
        if direction == Directions.TOP:
            self.progress += 0.01  # increase the progress with each TOP event
            self.io.send_progress(self.progress)  # and update the game engine

    # implement the required reset method
    async def reset(self, seat=0):
        pass


class AdvancedGame(Game):
    """
    Advanced game documentation2
    """

    async def on_init(self):
        # During the Game initialization callback register your joystick so
        # the Game Engine knows where to send the user input during the
        # games. Make sure that the name matches with the admin panel one.
        self.io.register_inputs({"joystick": MyJoystick(self.io)})

    async def on_config(self):
        # Do things before the game engine starts fetching new players
        pass

    async def on_prepare(self):
        # Do some preparations before the players connect
        pass

    async def on_pre_game(self):
        # Do some preparations after the players connect
        pass

    async def on_countdown(self):
        # Do things during the game countdown
        pass

    async def on_start(self):
        # Inputs are now enabled. Scores, laps and progress are counted

        if True:  # TODO create a score increasing condition
            self.io.send_score(100)
        pass

    async def on_finish(self):
        # Do something when the robot finishes the game
        pass

    async def on_exit(self, reason, exception):
        # This method is called just before the program exits
        pass


# And now you are ready to play!
if __name__ == "__main__":
    AdvancedGame().run()


# More info about:
# Game: https://docs.surrogate.tv/modules/surrortg.html#module-surrortg.game # noqa: E501
# Joystick: https://docs.surrogate.tv/modules/surrortg.inputs.html#module-surrortg.inputs.joystick # noqa: E501
# Inputs: https://docs.surrogate.tv/modules/surrortg.inputs.html
# More examples and the full documentation: https://docs.surrogate.tv/game_development.html # noqa: E501
