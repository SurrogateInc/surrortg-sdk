import asyncio
import logging
import time

from surrortg.image_recognition.aruco import ArucoFinder


# TODO some cleanup function when a template is changed
# for example: to stop the ArucoFinder running if not used
class GameTemplate:
    def __init__(self, hw, io):
        self.hw = hw
        self.io = io

    async def on_start(self):
        pass

    async def on_finish(self):
        return 1


class ExplorationGame(GameTemplate):
    async def on_start(self):
        await asyncio.sleep(30)
        return 1


class RacingGame(GameTemplate):
    async def on_config(self):
        # initialize ArucoFinder if does not exist
        if not hasattr(self, "finder"):
            self.finder == await ArucoFinder.create(
                self.io, num_markers=2, in_order=True, num_laps=2
            )
        self.finder.on_config(self.configs)

    async def on_start(self):
        # start the aruco finder
        self.finder.on_start()

        # color sensor checking code
        start_time = time.time()
        self.hw.color_sensor.active = True
        while True:
            await asyncio.sleep(0.5)
            temp_text = f"CPU: {self.hw.get_cpu_temperature()} C"
            self.hw.right_eye.write(temp_text)
            logging.info(temp_text)
            lux = self.hw.color_sensor.lux
            lux_text = f"lux: {lux}"
            self.hw.left_eye.write(lux_text)
            logging.info(lux_text)
            if lux is not None and lux > 800:
                end_time = time.time()
                return end_time - start_time

    async def on_finish(self):
        self.hw.color_sensor.active = False
        self.hw.reset_eyes()


class ObjectHuntGame(GameTemplate):
    async def on_config(self):
        # initialize ArucoFinder if does not exist
        if not hasattr(self, "finder"):
            self.finder == await ArucoFinder.create(
                self.io, num_markers=3, in_order=False
            )
        self.finder.on_config(self.configs)

    async def on_start(self):
        # start the aruco finder
        self.finder.on_start()

        await asyncio.sleep(60)
        return 0
