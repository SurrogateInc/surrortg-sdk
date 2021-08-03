import asyncio
import logging
from string import Template

import numpy as np

from surrortg.game_io import ConfigType

# How much difference we tolerate when reusing calibration marker locations(px)
CALIBRATION_SLACK_PARAM = 3

# How much leeway we have for detecting whether marker is inside area (in px)
LOC_SLACK_PARAM = 55 * 55

# Extra margin when cropping calibration markers out of frame
CROP_MARGIN = 20

LOC_SLACK_K = (
    "Virtual grid detection accuracy (higher means easier to hit target)"
)
CALIBR_ID_TEMPLATE = Template(
    "Virtual grid: Aruco marker ID for $pos calibration marker"
)
CALIBR_TOP_LEFT_KEY = CALIBR_ID_TEMPLATE.substitute(pos="top left")
CALIBR_TOP_RIGHT_KEY = CALIBR_ID_TEMPLATE.substitute(pos="top right")
CALIBR_BOTTOM_RIGHT_KEY = CALIBR_ID_TEMPLATE.substitute(pos="bottom right")
CALIBR_BOTTOM_LEFT_KEY = CALIBR_ID_TEMPLATE.substitute(pos="bottom left")
CUSTOM_KEY = "custom"


def point_in_rect(point, corners, slack_param=LOC_SLACK_PARAM):
    return point_estimate(point, corners) - slack_param <= 0


def point_estimate(point, corners):
    tot_area_w_point = 0
    for i in range(len(corners)):
        a = corners[i].tolist()
        b = point
        c = corners[i - 1].tolist()
        area = (
            abs(
                a[0] * (b[1] - c[1])
                + b[0] * (c[1] - a[1])
                + c[0] * (a[1] - b[1])
            )
            / 2
        )

        tot_area_w_point += area
    a = corners[1].tolist()
    b = corners[2].tolist()
    c = corners[3].tolist()
    area_of_rect = abs(
        a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1])
    )
    return tot_area_w_point - area_of_rect


class ArucoGrid:
    """Creates virtual grid of squares based on four aruco markers

    Why use this system:

        - If you need to have the game area divided into squares, you can use
          this system to automatically calibrate and create a virtual grid for
          you with the help of aruco markers.
        - No need to hardcode the grid using manually obtained pixel values.
        - The grid is generated every time a new game starts, so the grid will
          be correct even if the camera or game area is moved slightly; with
          hardcoded values even small misalignment can make the game unplayable

    How to use this system:

    1. Position four aruco markers at the corners of the physical game area::

         ------------------------------------
         |      |                   |       |
         |  1   |                   |   2   | <-- aruco marker
         |------|    GAME           |-------|
                |    AREA           |
         |------|                   |-------|
         |   4  |                   |   3   |
         |      |                   |       |
         ------------------------------------

    2. Create an ArucoGrid and pass the grid size (how many squares
        per side), an ArucoDetect instance, and the IDs of the corner
        markers (in order: top left, top right, bottom right, bottom left)
        to the ArucoGrid constructor.

    3. Call the generate_grid method (remember to use await). Once the
        method returns, the grid had been successfully generated. To
        prevent issues from camera misalignment, it's best to call
        calibrate always before game starts.

    4. Get position of the target(s) you wish to track, and use the
        point_in_rect method (or function) to detect whether the point is
        inside a specific square in the grid. (You can use the ArucoFinder
        class to track aruco markers in the game, or create your own logic,
        or even use the position of something other than an aruco marker)

    Short example of how to integrate the system into game logic:

    .. code-block:: python

        from surrortg.image_recognition.aruco import ArucoGrid

        YourGame(Game):
        async def on_init(self):
            self.grid_size = 4
            self.player_id = 0
            self.num_squares = self.grid_size**2
            self.aruco_source = await ArucoDetect().create()
            corners = [1, 2, 3, 4]
            self.grid = ArucoGrid(self.grid_size, self.aruco_source, corners)

        async def on_prepare(self):
            await self.grid.generate_grid()

        async def on_start(self):
            self.cur_sq_idx = random.randint(0, self.num_squares - 1)
            self.aruco_source.register_observer(self.aruco_found)

        def aruco_found(self, markers):
            for marker in markers:
                if marker.id != self.player_id:
                    continue
                if self.grid.point_in_sq(marker.get_location(), cur_sq_idx):
                    # point is inside currently active square: do something
                    # - increase score?
                    # - choose new square idx?

    Some notes about the system:

    - Three markers would be enough to provide full functionality, but we
      include a fourth marker so we know that the grid hasn't moved even when
      one of the markers is not visible. This way the calibration step can
      be concluded with one marker occluded, once the initial calibration has
      been done with four markers. This keeps the downtime low for games
      where the corner markers can be covered by cables etc.
    - The system may not work well if exact location data is needed with
      pixel presition. It is built with gameplay logic as the main priority.
      The detection accuracy parameter exists to make gameplay feel smooth
      even though the tracked target may not be exactly at the target
      location.

    :param grid_size: Number of squares per side (i.e. 3 -> 3x3 grid)
    :type grid_size: Int
    :param aruco_source: An ArucoDetect which the ArucoGrid subscribes to
        in order to receive detected aruco markers
    :type aruco_source: ArucoDetect
    :param ids: The IDs of the four corner markers. Must be given in the
        order: top left, top right, bottom right, bottom left
    :type ids: list of ints
    :param loc_slack: Detection accuracy. Used when checking if a point is
        inside a square. Higher number increases the probability a point is
        considered to be inside a square. This can be changed in the web
        configuration interface if generate_configs() and handle_configs()
        are called. (A value of ~3000 has been OK in testing)
    :type loc_slack: int
    :param crop_frame: Frames used to detect aruco markers are cropped
        so that the corner markers are left out of the frame after the grid
        has been generated. This imnproves performance, but may be unwanted
        in some cases.
    :type crop_frame: bool, optional
    """

    # IDs must be in the order: top left, top right, bottom right, bottom left
    def __init__(
        self,
        grid_size,
        aruco_source,
        ids=[46, 47, 48, 49],
        loc_slack=LOC_SLACK_PARAM,
        crop_frame=True,
    ):
        self.area_dim = grid_size
        self.calibration_done = False
        self._set_ids(ids)
        self.calibration_coords = {}
        self.new_calibration_coords = {}
        self.aruco_source = aruco_source
        self.loc_slack = loc_slack
        self.cropping_enabled = crop_frame

    def generate_configs(self, io):
        """Optional method for generating configs for the web config interface.

        This method should be called at the on_init part of the game loop in
        order to access corner marker IDs and detection accuracy in the web
        configuration interface.

        :param io: self.io passed from the game code
        :type io: GameIO
        """
        io.register_config(
            CALIBR_TOP_LEFT_KEY,
            ConfigType.INTEGER,
            self.top_left,
            False,
            minimum=0,
            maximum=49,
        )
        io.register_config(
            CALIBR_TOP_RIGHT_KEY,
            ConfigType.INTEGER,
            self.top_right,
            False,
            minimum=0,
            maximum=49,
        )
        io.register_config(
            CALIBR_BOTTOM_RIGHT_KEY,
            ConfigType.INTEGER,
            self.bottom_right,
            False,
            minimum=0,
            maximum=49,
        )
        io.register_config(
            CALIBR_BOTTOM_LEFT_KEY,
            ConfigType.INTEGER,
            self.bottom_left,
            False,
            minimum=0,
            maximum=49,
        )
        io.register_config(
            LOC_SLACK_K,
            ConfigType.INTEGER,
            LOC_SLACK_PARAM,
            False,
            minimum=1,
            maximum=10000,
        )

    def handle_configs(self, configs):
        """Optional method for handling configs from the web config interface.

        generate_configs() must be called before calling this function!
        This method should be called at the on_config part of the game loop in
        order to use corner marker IDs and detection accuracy from the web
        configuration interface.

        :param configs: self.configs from the Game object which owns this
            instance
        :type configs: dict
        """
        if CALIBR_TOP_LEFT_KEY not in configs[CUSTOM_KEY]:
            logging.warning(
                "ArucoGrid.handle_configs() called without calling"
                "ArucoGrid.generate_configs at on_init(). Unable to use custom"
                " calibration IDs!"
            )
        ids = []
        ids.append(configs[CUSTOM_KEY][CALIBR_TOP_LEFT_KEY])
        ids.append(configs[CUSTOM_KEY][CALIBR_TOP_RIGHT_KEY])
        ids.append(configs[CUSTOM_KEY][CALIBR_BOTTOM_RIGHT_KEY])
        ids.append(configs[CUSTOM_KEY][CALIBR_BOTTOM_LEFT_KEY])
        self._set_ids(ids)
        self.loc_slack = configs[CUSTOM_KEY][LOC_SLACK_K]

    async def generate_grid(self):
        """Generates the virtual grid.

        This method will return once the grid has been successfully created.
        This method should be called every time before the game starts to make
        sure the grid is calibrated for the current camera position. Remember
        to call this method with await!

        The return value is not required to use the system: only save it if
        implementing custom logic for the grid.

        :return: pixel coordinates for the corners of all the squares in the
            grid
        :rtype: array of array of floats
        """
        self.calibration_done = False
        self.new_calibration_coords = {}
        self.crop_params = (0, 0, 0, 0)
        self.aruco_source.set_crop(self.crop_params)
        self.aruco_source.register_observer(self._detect_cb)
        while not self.calibration_done:
            await asyncio.sleep(0.5)
        logging.info(
            f"grid generated - origin: {self.origin}, uvx: {self.unitv_x},"
            f" uvy: {self.unitv_y}"
        )

        return self.squares

    def point_in_sq(self, point, sq_idx):
        """Checks if point is inside square of given index.

        This method checks if the given point is inside a square of the grid
        generated in the generate_grid() method.

        :param point: point in the game area in pixel coordinates
        :type point: tuple of two floats
        :param sq_idx: index of the square to check against
        :type sq_idx: int

        :return: whether the point is inside the square
        :rtype: bool
        """
        if sq_idx > len(self.squares) - 1:
            logging.warning(
                f"ArucoGrid point_in_rect called with too high"
                f"index: {sq_idx} when number of squares is"
                f"{len(self.squares)}"
            )
            return False
        return point_in_rect(point, self.squares[sq_idx], self.loc_slack)

    def get_sq_idx(self, point):
        """Gets the square index for the point.

        :param point: point in the game area in pixel coordinates
        :type point: tuple of two floats

        :return: index of the square the point is in. Returns -1 if the point
            is not inside any of the squares.
        :rtype: int
        """
        indices = {}
        for sq in range(self.area_dim ** 2):
            comparison = (
                point_estimate(point, self.squares[sq]) - self.loc_slack
            )
            if comparison < 0:
                indices[sq] = comparison
        if len(indices) > 0:
            return min(indices, key=indices.get)
        return -1

    def _detect_cb(self, found_markers):
        for marker in found_markers:
            if (
                marker.id not in self.ids
                or marker.id in self.new_calibration_coords
                or len(self.new_calibration_coords) == len(self.ids)
            ):
                continue
            logging.info(
                f"calibration id {marker.id} with location "
                f"{marker.get_location()}"
            )
            self._add_calibration_marker(marker)

    def _coords_roughly_equal(self, old, new):
        return (
            abs(old[0] - new[0]) < CALIBRATION_SLACK_PARAM
            and abs(old[1] - new[1]) < CALIBRATION_SLACK_PARAM
        )

    def _corners_roughly_equal(self, old, new):
        num_equal_corners = 0
        for i in range(len(new)):
            num_equal_corners += int(
                self._coords_roughly_equal(old[i], new[i])
            )
        return num_equal_corners == 4

    def _generate_corners(self, origin, unitv_x, unitv_y, s_x, s_y):
        corner_a = origin + s_x * unitv_x + s_y * unitv_y
        corner_b = origin + (s_x + 1) * unitv_x + s_y * unitv_y
        corner_c = origin + (s_x + 1) * unitv_x + (s_y + 1) * unitv_y
        corner_d = origin + s_x * unitv_x + (s_y + 1) * unitv_y
        return [corner_a, corner_b, corner_c, corner_d]

    def _generate_corners_for_idx(self, idx, dim):
        y = idx // dim
        x = idx % dim
        return self._generate_corners(
            self.origin, self.unitv_x, self.unitv_y, x, y
        )

    def _generate_all_corners(self, dim):
        return [
            self._generate_corners_for_idx(i, dim) for i in range(dim ** 2)
        ]

    def _add_calibration_marker(self, marker):
        if self.calibration_done:
            self.aruco_source.unregister_observer(self._detect_cb)
            return
        self.new_calibration_coords[marker.id] = marker.corners
        if len(self.new_calibration_coords) == 4:
            self.aruco_source.unregister_observer(self._detect_cb)
            self.calibration_coords = self.new_calibration_coords
            self._generate_grid(self.calibration_coords)
        elif (
            len(self.new_calibration_coords) >= 3
            and len(self.calibration_coords) == 4
        ):
            num_roughly_equals_markers = 0
            for key in self.new_calibration_coords.keys():
                old_val = self.calibration_coords[key]
                new_val = self.new_calibration_coords[key]
                if self._corners_roughly_equal(old_val, new_val):
                    num_roughly_equals_markers += 1
            if num_roughly_equals_markers >= 3:
                logging.info("using old calibration marker locations")
                self.aruco_source.unregister_observer(self._detect_cb)
                self._generate_grid(self.calibration_coords)

    def _generate_grid(self, markers):
        if self.cropping_enabled:
            self._crop_frame()
        top_right = np.array([])
        bottom_left = np.array([])
        for key, corners in markers.items():
            if key == self.top_left:
                self.origin = np.array(
                    [
                        corners[1][0] - self.crop_params[1],
                        corners[1][1] - self.crop_params[3],
                    ]
                )
            elif key == self.top_right:
                top_right = np.array(
                    [
                        corners[0][0] - self.crop_params[1],
                        corners[0][1] - self.crop_params[3],
                    ]
                )
            elif key == self.bottom_left:
                bottom_left = np.array(
                    [
                        corners[2][0] - self.crop_params[1],
                        corners[2][1] - self.crop_params[3],
                    ]
                )

        self.unitv_x = (top_right - self.origin) / self.area_dim
        self.unitv_y = (bottom_left - self.origin) / self.area_dim
        self.squares = self._generate_all_corners(self.area_dim)
        self.calibration_done = True

    def _crop_frame(self):
        # Crop corner markers out of frame
        top_l, top_r, bot_r, bot_l = 0, 1, 2, 3
        top_left_m = self.calibration_coords[self.top_left]
        top_right_m = self.calibration_coords[self.top_right]
        bottom_right_m = self.calibration_coords[self.bottom_right]
        bottom_left_m = self.calibration_coords[self.bottom_left]

        max_x = (
            min(top_right_m[top_l][0], bottom_right_m[bot_l][0]) + CROP_MARGIN
        )
        min_x = (
            max(top_left_m[top_r][0], bottom_left_m[bot_r][0]) - CROP_MARGIN
        )
        max_y = (
            min(bottom_right_m[bot_l][1], bottom_left_m[bot_r][1])
            + CROP_MARGIN
        )
        min_y = max(top_left_m[top_r][1], top_right_m[top_l][1]) - CROP_MARGIN

        self.crop_params = (max_x, min_x, max_y, min_y)
        self.aruco_source.set_crop(self.crop_params)
        logging.info(f"new crop_params: {self.crop_params}")

    def _set_ids(self, ids):
        self.ids = ids
        self.top_left = ids[0]
        self.top_right = ids[1]
        self.bottom_right = ids[2]
        self.bottom_left = ids[3]
