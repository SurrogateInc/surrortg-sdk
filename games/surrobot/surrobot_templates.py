import logging
import os
import time

from games.surrobot.surrobot_config import Extension, Slot
from games.surrobot.surrobot_inputs import CallbackObjType
from surrortg import ScoreType, SortOrder
from surrortg.custom_overlay import (
    TimerType,
    custom_text_element,
    overlay_config,
    player_list,
    timer,
)
from surrortg.game_io import ConfigType

if os.getenv("MOCK_HW", False):
    from games.surrobot.mock_hw import MockArucoFilter as ArucoFilter
    from games.surrobot.mock_hw import MockOledImage as OledImage
else:
    from surrortg.devices.oled.assets import OledImage
    from surrortg.image_recognition.aruco import ArucoFilter

# Side length of aruco marker in millimeters
# TODO: move this elsewhere?
DEFAULT_MARKER_SIZE = 75

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

    def call_eyes(self, image_enum):
        self.game.hw.def_img_to_eyes(image_enum)

    def custom_overlay(self):
        return overlay_config([], {})

    def show_image_led_matrix(self, image="surrobot-logo-even-bigger"):
        matrix = self.game.hw.led_matrix
        if matrix.enabled:
            matrix.show_image(image)

    def aruco_distance_filter(self, marker):
        """Filter aruco markers based on physical distance

        Uses a magic formula to fix measurement error. Magic formula unlikely
        to work with other cameras.

        param marker: aruco marker
        type: ArucoMarker
        """
        distance = marker.get_real_distance(
            self.marker_size * 1000,
            self.game.hw.sensor_height,
            self.game.hw.focal_length,
        )
        # Fix measurement errors due to fish eye lens and other imperfections.
        # Formula is based on observed data, no theoretical backing.
        correction = (
            (200 / self.marker_size) ** 1.9 * (distance / 200) ** 1.11
        ) ** 1.1
        fixed_distance = distance - correction
        # convert max distance to millimeters
        return fixed_distance < self.aruco_max_distance * 10

    async def input_callback(self, slot, extension, obj):
        pass

    async def on_template_selected(self):
        pass

    async def on_config(self):
        pass

    async def on_start(self):
        pass

    async def on_finish(self):
        pass


class ExplorationGame(GameTemplate):
    def slot_limits(self):
        return {
            Slot.TOP_FRONT: {
                "default": Extension.DISABLED,
                "extensions": [
                    Extension.CAMERA_2_AXIS,
                    Extension.BUTTON_PRESSER,
                    Extension.DISABLED,
                ],
            },
            Slot.TOP_BACK: {
                "default": Extension.DISABLED,
                "extensions": [
                    Extension.BUTTON_PRESSER,
                    Extension.DISABLED,
                ],
            },
            Slot.BOTTOM_FRONT: {
                "default": Extension.DISABLED,
                "extensions": [
                    Extension.BUTTON_PRESSER,
                    Extension.DISABLED,
                ],
            },
        }

    def custom_overlay(self):
        return overlay_config([player_list(), timer(TimerType.REMAINING)])

    async def on_config(self):
        # Set correct score type and order
        await self.game.io.set_score_type(
            ScoreType.TOTAL_GAMES, SortOrder.DESCENDING
        )
        self.show_image_led_matrix()
        self.game.hw.reset_eyes()

    async def on_start(self):
        self.game.io.send_score(score=1)


class CustomGame(GameTemplate):
    async def on_start(self):
        logging.info("CustomGame on_start")

    async def on_config(self):
        self.show_image_led_matrix()


class StarterGame(GameTemplate):
    def slot_limits(self):
        return {
            Slot.MOVEMENT: {
                "default": Extension.DISABLED,
                "extensions": [
                    Extension.DRIVE_4_WHEELS,
                    Extension.DISABLED,
                ],
            },
            Slot.TOP_FRONT: {
                "default": Extension.DISABLED,
                "extensions": [
                    Extension.CAMERA_2_AXIS,
                    Extension.DISABLED,
                ],
            },
            Slot.TOP_BACK: {
                "default": Extension.DISABLED,
                "extensions": [
                    Extension.BUTTON_PRESSER,
                    Extension.DISABLED,
                ],
            },
            Slot.BOTTOM_FRONT: {
                "default": Extension.BUTTON_PRESSER,
                "extensions": [
                    Extension.BUTTON_PRESSER,
                    Extension.DISABLED,
                ],
            },
        }

    def custom_overlay(self):
        return overlay_config([player_list(), timer(TimerType.REMAINING)])

    async def on_start(self):
        logging.info("Starter on_start")
        self.game.io.send_score(score=1)

    async def on_config(self):
        # Set correct score type and order
        await self.game.io.set_score_type(
            ScoreType.TOTAL_GAMES, SortOrder.DESCENDING
        )
        self.show_image_led_matrix()
        self.game.hw.reset_eyes()

    # TODO: better handling
    async def input_callback(self, slot, extension, obj):
        logging.info(f"input cb slot {slot} ext {extension} obj {obj}")
        if obj.type == CallbackObjType.BUTTON:
            if obj.is_on:
                self.call_eyes(OledImage.DOING_ACTION)
            else:
                self.game.hw.reset_eyes()


class RacingGame(GameTemplate):
    def __init__(self, game):
        super().__init__(game)
        self.filter = None
        self.aruco_max_distance = 100
        self.marker_size = DEFAULT_MARKER_SIZE

    def game_configs(self):
        return {
            "maxLaps": {
                "title": "Number of laps",
                "valueType": ConfigType.INTEGER,
                "default": 3,
                "minimum": 1,
                "maximum": 10,
            },
            "maxMarkers": {
                "title": "Number of markers",
                "valueType": ConfigType.INTEGER,
                "default": 3,
                "minimum": 3,
                "maximum": 50,
            },
            "arucoDetectionDistance": {
                "title": "Aruco Marker Detection Distance (cm)",
                "valueType": ConfigType.INTEGER,
                "default": 100,
                "minimum": 20,
                "maximum": 300,
            },
            # TODO: support inches as well?
            "arucoMarkerSize": {
                "title": "Size of Aruco Markers (millimeters)",
                "valueType": ConfigType.INTEGER,
                "default": DEFAULT_MARKER_SIZE,
                "minimum": 10,
                "maximum": 200,
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

    # TODO: implement this for other templates/abstract this
    async def input_callback(self, slot, extension, obj):
        if (
            slot is Slot.MOVEMENT
            and obj.type == CallbackObjType.JOYSTICK
            and obj.limit_to == "x"
        ):
            if obj.x < -0.5:
                self.call_eyes(OledImage.RACING_TURN_L)
            elif obj.x > 0.5:
                self.call_eyes(OledImage.RACING_TURN_R)
            else:
                self.call_eyes(OledImage.RACING_STRAIGHT)
        elif obj.type == CallbackObjType.BUTTON:
            if obj.is_on:
                self.call_eyes(OledImage.DOING_ACTION)
            else:
                self.call_eyes(OledImage.RACING_STRAIGHT)

    def custom_overlay(self):
        return overlay_config(
            [player_list(), timer(TimerType.ELAPSED)],
            {"laps": custom_text_element("Lap Count")},
        )

    async def on_template_selected(self):
        self.filter = ArucoFilter(
            self.marker_callback,
            self.game.aruco_source,
            detection_cooldown=0.5,
        )
        self.filter.add_filter(self.aruco_distance_filter)

    async def on_config(self):
        # Set correct score type and order
        await self.game.io.set_score_type(
            ScoreType.TIMESTAMP, SortOrder.ASCENDING
        )

        # Store custom configs
        self.max_laps = self.game.config_parser.get_game_config("maxLaps")
        self.max_markers = self.game.config_parser.get_game_config(
            "maxMarkers"
        )
        self.aruco_max_distance = self.game.config_parser.get_game_config(
            "arucoDetectionDistance"
        )
        self.marker_size = self.game.config_parser.get_game_config(
            "arucoMarkerSize"
        )

        self.show_image_led_matrix("racing")
        self.game.hw.reset_eyes()

    def update_lap_overlay(self):
        current_lap = max(1, min(self.lap, self.max_laps))
        lap_text = f"Lap {current_lap}/{self.max_laps}"
        self.game.io.set_custom_overlay_text("laps", lap_text)

    async def on_start(self):
        self.start_time = time.perf_counter()
        self.lap = 0
        self.next_marker = 1
        self.filter.ids = [1]
        self.filter.start()
        self.update_lap_overlay()
        self.call_eyes(OledImage.RACING_STRAIGHT)

    async def on_finish(self):
        self.game.io.disable_inputs()
        self.game.hw.reset_eyes()
        self.filter.stop()

    def marker_callback(self, marker):
        logging.info(f"Marker {marker.id} found")

        # If start/finish line was found
        if marker.id == 1:
            self.lap += 1
            logging.info(f"Lap {self.lap}/{self.max_laps}")
            self.update_lap_overlay()

        # If last lap was finished
        if self.lap > self.max_laps:
            time_ms = self.seconds_to_ms(time.perf_counter() - self.start_time)
            self.game.io.send_score(
                score=time_ms, seat=0, seat_final_score=True
            )
            self.filter.stop()
            logging.info("Race finished!")

        # If last marker was found
        if marker.id == self.max_markers:
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
    def __init__(self, game):
        super().__init__(game)
        self.filter = None
        self.aruco_max_distance = 100
        self.marker_size = DEFAULT_MARKER_SIZE

    async def on_template_selected(self):
        self.filter = ArucoFilter(
            self.marker_callback,
            self.game.aruco_source,
        )
        self.filter.add_filter(self.aruco_distance_filter)

    def game_configs(self):
        return {
            "maxMarkers": {
                "title": "Number of markers",
                "valueType": ConfigType.INTEGER,
                "default": 3,
                "minimum": 1,
                "maximum": 50,
            },
            "arucoDetectionDistance": {
                "title": "Aruco Marker Detection Distance (cm)",
                "valueType": ConfigType.INTEGER,
                "default": 100,
                "minimum": 20,
                "maximum": 300,
            },
            "arucoMarkerSize": {
                "title": "Size of Aruco Markers (side length, in millimeters)",
                "valueType": ConfigType.INTEGER,
                "default": DEFAULT_MARKER_SIZE,
                "minimum": 10,
                "maximum": 200,
            },
        }

    def slot_limits(self):
        return {
            Slot.MOVEMENT: {
                "default": Extension.DRIVE_4_WHEELS,
                "extensions": [
                    Extension.DRIVE_4_WHEELS,
                ],
            }
        }

    def custom_overlay(self):
        return overlay_config(
            [player_list(), timer(TimerType.REMAINING)],
            {"markers": custom_text_element("Markers Found")},
        )

    async def on_config(self):
        # Set correct score type and order
        await self.game.io.set_score_type(
            ScoreType.POINTS, SortOrder.DESCENDING
        )

        # Store custom configs
        self.max_markers = self.game.config_parser.get_game_config(
            "maxMarkers"
        )
        self.aruco_max_distance = self.game.config_parser.get_game_config(
            "arucoDetectionDistance"
        )
        self.game.hw.marker_size = self.game.config_parser.get_game_config(
            "arucoMarkerSize"
        )

        self.show_image_led_matrix("searching")
        self.game.hw.reset_eyes()

    def update_marker_overlay(self):
        found = self.max_markers - len(self.filter.ids)
        marker_text = f"Found {found}/{self.max_markers}"
        self.game.io.set_custom_overlay_text("markers", marker_text)

    async def on_start(self):
        self.filter.ids = list(range(1, self.max_markers + 1))
        self.filter.start()
        self.search_start_time = time.perf_counter()
        self.marker_max_score = 100
        self.total_score = 0
        self.update_marker_overlay()
        self.call_eyes(OledImage.ARUCO_DEF)

    async def on_finish(self):
        self.game.io.disable_inputs()
        self.game.hw.reset_eyes()
        self.filter.stop()

    def marker_callback(self, marker):
        logging.info(f"Marker {marker.id} found")

        # Calculate marker search time and reset clock
        search_end_time = time.perf_counter()
        search_time = search_end_time - self.search_start_time
        self.search_start_time = time.perf_counter()

        # Add score from current marker to total score and send it to the GE.
        # Score for each marker starts from marker maximum score and then
        # decays exponentially as time goes on.
        self.total_score += self.marker_max_score * (1 - 0.0228) ** search_time
        self.game.io.send_score(round(self.total_score, 2))

        # Mark filter as found
        self.filter.ids.remove(marker.id)
        self.update_marker_overlay()

        # If last marker was found
        if not self.filter.ids:
            self.game.io.send_score(
                score=round(self.total_score, 2), seat_final_score=True
            )
            self.filter.stop()
            logging.info("All markers found!")
        else:
            logging.info(f"{len(self.filter.ids)} markers left")
