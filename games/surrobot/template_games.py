import asyncio
import logging
import time


class GameTemplate:
    def __init__(self, hw):
        self.hw = hw

    async def on_start(self):
        pass

    async def on_finish(self):
        return 1


class Game1(GameTemplate):
    async def on_start(self):
        await asyncio.sleep(5)
        return 1


class RacingGame(GameTemplate):
    async def on_start(self):
        start_time = time.time()
        self.hw.color_sensor.active = True
        while True:
            await asyncio.sleep(0.5)
            lux = self.hw.color_sensor.lux
            text = f"lux: {lux}"
            self.hw.left_eye.write(text)
            logging.info(text)
            if lux is not None and lux > 800:
                end_time = time.time()
                return end_time - start_time

    async def on_finish(self):
        self.hw.color_sensor.active = False
        self.hw.reset_eyes()


class Game3(GameTemplate):
    async def on_start(self):
        await asyncio.sleep(10)
        return 0
