import asyncio
import random
import time

from games.m5_rover.m5_rover import M5Rover
from surrortg import Game
from surrortg.devices.led_matrix import LedMatrix
from surrortg.game_io import ConfigType
from surrortg.image_recognition.aruco import ArucoDetector, ArucoGrid

INITIAL_GAME_TIME = 25

GAME_AREA_SIZE_KEY = "Game area side length (number of squares)"
INITIAL_GAME_TIME_KEY = "Initial game time"
GAME_TIME_REDUCE_KEY = "Time change after success"
MIN_GAME_TIME_KEY = "Lower limit for time to reach target"
CUSTOM_KEY = "custom"
ARUCO_ID_KEY = "Aruco ID for player marker"
RESTART_TIMER_KEY = "Restart timer after success (+/- time change)"

DEF_GAME_AREA_SIZE = 4

# TODO: change this to local config
ARUCO_CAMERA_PATH = (
    "/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_"
    "Camera_SN0001-video-index0"
)


class Timer:
    def __init__(self, callback, timeout):
        self.callback = callback
        self.timeout = timeout
        self.task = asyncio.create_task(self._job())

    async def _job(self):
        try:
            await asyncio.sleep(self.timeout)
            await self.callback()
        except asyncio.CancelledError:
            pass

    def cancel(self):
        if self.task is not None:
            if not self.task.done():
                self.task.cancel()
            self.task = None


class ColorCatcher(Game):
    """See the README file for instructions"""

    async def on_init(self):
        self.io.register_config(
            INITIAL_GAME_TIME_KEY,
            ConfigType.INTEGER,
            INITIAL_GAME_TIME,
            False,
            minimum=6,
            maximum=60,
        )
        self.io.register_config(
            GAME_TIME_REDUCE_KEY,
            ConfigType.INTEGER,
            -2,
            False,
            minimum=-10,
            maximum=10,
        )
        self.io.register_config(
            GAME_AREA_SIZE_KEY,
            ConfigType.INTEGER,
            DEF_GAME_AREA_SIZE,
            False,
            minimum=1,
            maximum=16,
        )
        self.io.register_config(
            MIN_GAME_TIME_KEY,
            ConfigType.INTEGER,
            4,
            False,
            minimum=1,
            maximum=30,
        )
        self.io.register_config(
            ARUCO_ID_KEY, ConfigType.INTEGER, 0, False, minimum=0, maximum=45
        )
        self.io.register_config(
            RESTART_TIMER_KEY, ConfigType.BOOLEAN, True, False
        )

        self.led_matrix = LedMatrix(self.io, DEF_GAME_AREA_SIZE)

        self.m5_rover = M5Rover(
            self.io, throttle_mult=0.3, steering_mult=1, sideways_mult=0.5
        )
        self.io.register_inputs(self.m5_rover.inputs)
        self.aruco_source = await ArucoDetector.create(
            source=ARUCO_CAMERA_PATH
        )
        self.grid = ArucoGrid(
            DEF_GAME_AREA_SIZE, self.aruco_source, [46, 47, 48, 49]
        )
        self.grid.generate_configs(self.io)
        self.in_game = False
        self.cur_area_idx = 0
        self.timer = None

    async def on_config(self):
        # We omit checking if these exists as the game will not work without
        # the configs anyway.
        self.area_dim = self.configs[CUSTOM_KEY][GAME_AREA_SIZE_KEY]
        self.led_matrix.set_size(self.area_dim)
        self.num_squares = self.area_dim ** 2
        self.reduce_time = self.configs[CUSTOM_KEY][GAME_TIME_REDUCE_KEY]
        self.lower_time_limit = self.configs[CUSTOM_KEY][MIN_GAME_TIME_KEY]
        self.restart_timer = self.configs[CUSTOM_KEY][RESTART_TIMER_KEY]
        self.bot_aruco_id = self.configs[CUSTOM_KEY][ARUCO_ID_KEY]
        self.led_matrix.handle_config(self.configs)
        self.grid.handle_configs(self.configs)
        await self.m5_rover.handle_config(self.configs)

    async def on_prepare(self):
        self.cur_area_idx = random.randint(0, self.num_squares - 1)
        await self.grid.generate_grid()

    async def on_countdown(self):
        await self.led_matrix.countdown()

    async def on_start(self):
        self.aruco_source.register_observer(self.aruco_coord_cb)
        self.time = self.configs[CUSTOM_KEY][INITIAL_GAME_TIME_KEY]
        self.prev_success_time = time.time()
        self.score = 0
        self.set_new_area()
        self.in_game = True

    async def end_game(self):
        if not self.in_game:
            return
        self.in_game = False
        self.io.send_score(score=self.score, seat=0, final_score=True)
        self.led_matrix.end_game()
        self.aruco_source.unregister_observer(self.aruco_coord_cb)

    def aruco_coord_cb(self, markers):
        for marker in markers:
            if not self.in_game or marker.id != self.bot_aruco_id:
                continue
            if self.grid.point_in_sq(marker.get_location(), self.cur_area_idx):
                self.handle_score()

    def next_area_idx(self, cur_idx, area_count):
        next_idx = cur_idx
        while next_idx == cur_idx:
            next_idx = random.randint(0, area_count - 1)
        return next_idx

    def set_new_area(self):
        self.cur_area_idx = self.next_area_idx(
            self.cur_area_idx, self.num_squares
        )
        self.led_matrix.set_timed_area(self.cur_area_idx, self.time)
        self.timer = Timer(self.end_game, self.time)

    def handle_score(self):
        if not self.in_game:
            return
        self.timer.cancel()
        time_passed = 0
        if not self.restart_timer:
            time_passed = time.time() - self.prev_success_time
            self.prev_success_time = time.time()
        if self.time + self.reduce_time - time_passed >= self.lower_time_limit:
            self.time += self.reduce_time - time_passed
        else:
            self.time = self.lower_time_limit
        self.score += 1
        self.io.send_score(score=self.score, seat=0, final_score=False)
        self.set_new_area()

    async def on_exit(self, reason, exception):
        self.in_game = False
        if self.timer is not None:
            self.timer.cancel()
        self.led_matrix.on_exit()
        self.aruco_source.unregister_observer(self.aruco_coord_cb)


# And now you are ready to play!
if __name__ == "__main__":
    ColorCatcher().run()

# More info about:
# Game: https://docs.surrogate.tv/modules/surrortg.html#module-surrortg.game # noqa: E501
# Inputs: https://docs.surrogate.tv/modules/surrortg.inputs.html
# More examples and the full documentation: https://docs.surrogate.tv/game_development.html # noqa: E501
