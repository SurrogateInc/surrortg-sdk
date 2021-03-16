from games.rvr.rvr import RVR
from surrortg import Game


class RVRGame(Game):
    async def on_init(self):
        self.rvr = RVR()
        await self.rvr.init_sphero()
        self.io.register_inputs({"joystick_main": self.rvr})

    async def on_exit(self, reason, exception):
        await self.rvr.shutdown()


if __name__ == "__main__":
    RVRGame().run()
