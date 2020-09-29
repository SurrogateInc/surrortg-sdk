from surrortg import Game  # First we need import the Game
from surrortg.inputs import LinearActuator  # and our preferred input(s)
from surrortg.devices import Car  # and Car


# Create Motor and Steering classes, which handle Car's speed and direction
class Motor(LinearActuator):
    async def drive_actuator(self, val, seat=0):
        # TODO throttle implementation here
        pass

    async def reset(self, seat=0):
        await self.drive_actuator(0)


class Steering(LinearActuator):
    async def drive_actuator(self, val, seat=0):
        # TODO steer implementation here
        pass

    async def reset(self, seat=0):
        await self.drive_actuator(0)


class CarGame(Game):
    async def on_init(self):
        # Areate new Motor and Steering instances
        motor = Motor()
        steering = Steering()
        # And wrap the into a Car instance
        self.car = Car(steering, motor)

        # During the Game initialization callback register your motor and
        # steering so the Game Engine knows where to send the user input
        # during the games. Make sure that the names match with the admin
        # panel ones.
        self.io.register_inputs({"motor": motor, "steering": steering})


# And now you are ready to play!
CarGame().run()


# More info about:
# Game: <url>
# LinearActuator: <url>
# Car: <url>
# More examples and the full documentation: <url>
