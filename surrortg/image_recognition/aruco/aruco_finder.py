import logging

from surrortg.game_io import ConfigType

from .aruco_filter import ArucoFilter
from .aruco_source import ArucoDetector

DEFAULT_CAMERA = "/dev/video21"

CUSTOM_KEY = "custom"
NUM_MARKERS_KEY = "Number of aruco markers to find"
MIN_DISTANCE_KEY = "Minimum distance for detection (0 for any distance)"
IN_ORDER_KEY = "Markers must be detected in order"
IN_ORDER_DEF_VAL = False
NUM_LAPS_KEY = "Number of laps"


class ArucoFinder:
    @classmethod
    async def create(
        cls,
        io,
        source=DEFAULT_CAMERA,
        num_markers=5,
        min_distance=100,
        in_order=False,
        num_laps=1,
        bot_specific=False,
        seat=0,
    ):
        """Class for creating treasure hunt and racing games with aruco markers

        This class is an easy way to incorporate aruco markers into a game. The
        class creates its own ArucoDetector instance and has built-in game
        logic, so only a few lines of code are required to use the class.

        The class sends configuration options to the dashboard Game Engine
        settings, where the configuration parameters can be changed. For a
        racing type game, set in_order to True.

        Short example of how to integrate the class into game logic:

        .. code-block:: python

            from surrortg.image_recognition.aruco import ArucoFinder

            YourGame(Game):
            async def on_init(self):
                self.finder = await ArucoFinder.create(self.io)

            async def on_config(self):
                self.finder.on_config(self.configs)

            async def on_start(self):
                self.finder.on_start()

        :param io: GameIO instance, used to register configs and send scores
            to the game engine
        :type io: GameIO
        :param source: Video capture device used for detecting aruco markers
        :type source: string, optional
        :param num_markers: number of aruco IDs to use. IDs will be generated
            from 0 to num_markers-1
        :type num_markers: int
        :param min_distance: Distance threshold for detecting an aruco
            marker. This class uses an arbitrary unit of distance between 0 and
            500
        :type min_distance: float between 0 and 500, optional
        :param in_order: Whether markers must be detected in ascending
            numerical order. Useful for racing games
        :type in_order: bool, optional
        :param num_laps: Number of laps in one game
        :type num_laps: int, optional
        :param bot_specific: Whether the configuration options in the web
            interface are in effect for all bots, or just this bot
        :type bot_specific: bool, optional
        :param seat: Seat number of the bot
        :type seat: int, optional
        """
        self = cls()
        self.io = io
        self.seat = seat
        self.io.register_config(
            NUM_MARKERS_KEY,
            ConfigType.INTEGER,
            num_markers,
            bot_specific,
            minimum=1,
            maximum=50,
        )
        self.io.register_config(
            MIN_DISTANCE_KEY,
            ConfigType.INTEGER,
            min_distance,
            bot_specific,
            minimum=0,
            maximum=500,
        )
        self.io.register_config(
            NUM_LAPS_KEY,
            ConfigType.INTEGER,
            num_laps,
            bot_specific,
            minimum=1,
            maximum=100,
        )
        self.io.register_config(
            IN_ORDER_KEY, ConfigType.BOOLEAN, in_order, bot_specific
        )
        self.aruco_source = await ArucoDetector.create(source)
        self.filter = ArucoFilter(
            self._score_logic,
            self.aruco_source,
            self._gen_id_list(num_markers),
            min_distance,
        )
        return self

    def on_config(self, configs):
        """Parses the configs object for configs from web interface.

        MUST BE CALLED every time at the on_config part of the game loop.

        :param configs: self.configs from the Game object which owns this
            instance
        :type configs: dict
        """
        self.filter.stop()
        self.num_markers = configs[CUSTOM_KEY][NUM_MARKERS_KEY]
        if configs[CUSTOM_KEY][MIN_DISTANCE_KEY] == 0:
            self.filter.min_dist = 0
        else:
            self.filter.min_dist = 0.5 / configs[CUSTOM_KEY][MIN_DISTANCE_KEY]
        self.num_laps = configs[CUSTOM_KEY][NUM_LAPS_KEY]
        self.in_order = configs[CUSTOM_KEY][IN_ORDER_KEY]
        self.filter.ids = self._gen_id_list(self.num_markers)
        logging.info(
            f"ArucoFinder configured with markers: {self.filter.ids}"
            f" and minimum marker size: {self.filter.min_dist}"
        )

    def on_start(self):
        """Starts the aruco detection and begins counting scores. MUST BE
        CALLED every time at the on_start part of the game loop.
        """
        self.score = 0
        self.cur_lap = 1
        self.filter.start()

    def stop(self):
        """Call this at the on_exit part of the game loop.

        This ensures that the program exits correctly.
        """
        self.filter.stop()

    def _score_logic(self, marker):
        is_final = False
        if not self.in_order or (
            self.in_order and marker.id == min(self.filter.ids)
        ):
            self.filter.ids.remove(marker.id)
            self.score += 1
        if len(self.filter.ids) == 0:
            if self.cur_lap == self.num_laps:
                self.filter.stop()
                is_final = True
            else:
                self.cur_lap += 1
                self.filter.ids = self._gen_id_list(self.num_markers)
        self.io.send_score(self.score, seat=self.seat, final_score=is_final)

    def _gen_id_list(self, num_ids):
        return set(marker_id for marker_id in range(num_ids))
