from surrortg import Game

from .m5_rover import M5Rover


class M5SimpleGame(Game):
    async def on_init(self):
        self.m5_rover = M5Rover(self.io)
        self.io.register_inputs(self.m5_rover.inputs)

    async def on_config(self):
        set_num = await self.m5_rover.handle_config(self.configs)
        return set_num


if __name__ == "__main__":
    M5SimpleGame().run()
