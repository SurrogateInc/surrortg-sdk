import asyncio
import logging

from surrortg.image_recognition.aruco import ArucoFilter

MARKER_IDS = [1, 2, 3]
DETECT_DISTANCE = 0
LAPS = 3


# TODO some cleanup function when a template is changed
# for example: to stop the ArucoFinder running if not used
class GameTemplate:
    def __init__(self, game):
        self.game = game

    async def on_template_selected(self):
        pass

    async def on_config(self):
        pass

    async def on_start(self):
        pass

    async def on_finish(self):
        pass


class ExplorationGame(GameTemplate):
    async def on_start(self):
        await asyncio.sleep(30)
        self.game.io.send_score(score=1, final_score=True)


class RacingGame(GameTemplate):
    async def on_template_selected(self):
        self.filter = ArucoFilter(
            self.marker_callback,
            self.game.aruco_source,
            detection_cooldown=0.5,
        )
        self.lap = 1

    def marker_callback(self, marker):
        logging.info(f"marker {marker.id} found")
        if len(self.filter.ids) != 0 and marker.id == min(self.filter.ids):
            self.filter.ids.remove(marker.id)
            if len(self.filter.ids) == 0:
                self.lap += 1
                self.filter.ids = MARKER_IDS.copy()
                self.game.io.send_lap()  # ignored by ge currently
                if self.lap > LAPS:
                    logging.info("last lap finished!")
                    self.game.io.send_score(
                        score=1, seat=0, seat_final_score=True
                    )
                    return

            if self.lap <= LAPS:
                progress = round(1 - len(self.filter.ids) / len(MARKER_IDS), 2)
                logging.info(f"progress: {progress}, lap {self.lap}/{LAPS}")
                self.game.io.send_progress(progress)  # ignored by ge currently

    async def on_start(self):
        self.lap = 1
        self.filter.ids = MARKER_IDS.copy()
        self.filter.start()

        # color sensor checking code
        """
        start_time = time.time()
        self.game.hw.color_sensor.active = True
        while True:
            await asyncio.sleep(0.5)
            temp_text = f"CPU: {self.game.hw.get_cpu_temperature()} C"
            self.game.hw.right_eye.write(temp_text)
            logging.info(temp_text)
            lux = self.game.hw.color_sensor.lux
            lux_text = f"lux: {lux}"
            self.game.hw.left_eye.write(lux_text)
            logging.info(lux_text)
            if lux is not None and lux > 800:
                end_time = time.time()
                return end_time - start_time
        """

    async def on_finish(self):
        self.filter.stop()
        self.game.hw.color_sensor.active = False
        self.game.hw.reset_eyes()


class ObjectHuntGame(GameTemplate):
    async def on_template_selected(self):
        self.filter = ArucoFilter(
            self.marker_callback,
            self.game.aruco_source,
            detection_cooldown=0,
            detect_distance=DETECT_DISTANCE,
        )

    def marker_callback(self, marker):
        logging.info(f"marker {marker.id} found")
        self.filter.ids.remove(marker.id)
        if len(self.filter.ids) == 0:
            logging.info("All found!")
            self.game.io.send_score(score=1, final_score=True)
            return
        else:
            logging.info(f"{len(self.filter.ids)} markers left!")

    async def on_start(self):
        self.filter.ids = MARKER_IDS.copy()
        self.filter.start()
