import asyncio
import logging
import time

from games.surrobot.surrobot_config import Extension, Slot
from surrortg.game_io import ConfigType
from surrortg.image_recognition.aruco import ArucoFilter

# These are still used in ObjectHuntGame, to be replaced with new configs
MARKER_IDS = [1, 2, 3]
DETECT_DISTANCE = 0


# TODO some cleanup function when a template is changed
# for example: to stop the ArucoFinder running if not used
class GameTemplate:
    def __init__(self, game):
        self.game = game

    def description(self):
        return None

    def game_configs(self):
        return None

    def slot_limits(self):
        return None

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
    def game_configs(self):
        return {
            "maxLaps": {
                "title": "Number of laps",
                "valueType": ConfigType.INTEGER,
                "default": 3,
                "minimum": 1,
                "maximum": 10,
            },
            "markerCount": {
                "title": "Number of markers",
                "valueType": ConfigType.INTEGER,
                "default": 3,
                "minimum": 3,
                "maximum": 50,
            },
        }

    def slot_limits(self):
        return {
            Slot.MOVEMENT: {
                "default": Extension.DRIVE_4_WHEELS,
                "extensions": [
                    Extension.DRIVE_4_WHEELS,
                    Extension.DRIVE_2_WHEELS,
                ],
            }
        }

    async def on_template_selected(self):
        self.filter = ArucoFilter(
            self.marker_callback,
            self.game.aruco_source,
            detection_cooldown=0.5,
        )

    async def on_config(self):
        self.max_laps = self.game.config_parser.get_game_config("maxLaps")
        self.marker_count = self.game.config_parser.get_game_config(
            "markerCount"
        )

    async def on_start(self):
        self.start_time = time.perf_counter()
        self.lap = 0
        self.next_marker = 1
        self.filter.ids = [1]
        self.filter.start()

    async def on_finish(self):
        self.game.io.disable_inputs()
        self.filter.stop()
        self.game.hw.reset_eyes()

    def marker_callback(self, marker):
        logging.info(f"Marker {marker.id} found")

        # If start/finish line was found
        if marker.id == 1:
            self.lap += 1
            logging.info(f"Lap {self.lap}/{self.max_laps}")

        # If last lap was finished
        if self.lap > self.max_laps:
            time_ms = self.seconds_to_ms(time.perf_counter() - self.start_time)
            self.game.io.send_score(
                score=time_ms, seat=0, seat_final_score=True
            )
            logging.info("Race finished!")

        # If last marker was found
        if marker.id == self.marker_count:
            self.next_marker = 1
        else:
            self.next_marker += 1

        # Set new marker id
        self.filter.ids = [self.next_marker]

    def seconds_to_ms(self, seconds):
        ms = seconds * 1000
        rounded_ms = round(ms, 0)
        return rounded_ms


class ObjectHuntGame(GameTemplate):
    async def on_template_selected(self):
        self.filter = ArucoFilter(
            self.marker_callback,
            self.game.aruco_source,
            detection_cooldown=0,
            detect_distance=DETECT_DISTANCE,
        )

    def game_configs(self):
        return {
            "maxMarkers": {
                "title": "Amount of markers",
                "valueType": ConfigType.INTEGER,
                "default": 3,
                "minimum": 1,
                "maximum": 20,
            }
        }

    async def on_config(self):
        self.max_markers = self.game.config_parser.get_game_config(
            "maxMarkers"
        )

    def marker_callback(self, marker):
        logging.info(f"marker {marker.id} found")
        self.filter.ids.remove(marker.id)
        if len(self.filter.ids) == 0:
            logging.info("All found!")
            self.game.io.send_score(score=1, final_score=True)
        else:
            logging.info(f"{len(self.filter.ids)} markers left!")

    async def on_start(self):
        self.filter.ids = MARKER_IDS.copy()
        self.filter.start()
