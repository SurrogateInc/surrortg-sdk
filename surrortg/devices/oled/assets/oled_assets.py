import os
from enum import Enum, auto

ASSET_PATH = os.path.dirname(__file__)
FONT_PATH = os.path.join(ASSET_PATH, "FreeMono.ttf")

# How to add eye assets:
# - Add path enums for both eyes to OledImagePath; The enum name must end with
#   _L for left eye and _R for right eye! If using same image for both, just
#   add two enums pointing to same path (not tested).
# - Add image enum to OledImage. The enum name must match the path enum
#   excluding the "_R"/"_L" at the end.
#
# How to use eye assets:
# - Call oled_eye.show_default_image(OledImage.ENUM_HERE). The eye will choose
#   the path corresponding to its location (left/right)


class OledImagePath(Enum):
    DEFAULT_EYE_L = os.path.join(ASSET_PATH, "default_l_eye.png")
    DEFAULT_EYE_R = os.path.join(ASSET_PATH, "default_r_eye.png")
    BLINK_L = os.path.join(ASSET_PATH, "left_blink_long.gif")
    BLINK_R = os.path.join(ASSET_PATH, "right_blink_long.gif")
    ARUCO_DEF_L = os.path.join(ASSET_PATH, "aruco_game_default_left.png")
    ARUCO_DEF_R = os.path.join(ASSET_PATH, "aruco_game_default_right.png")
    RACING_STRAIGHT_L = os.path.join(ASSET_PATH, "drive_straight_left_eye.png")
    RACING_STRAIGHT_R = os.path.join(
        ASSET_PATH, "drive_straight_right_eye.png"
    )
    RACING_TURN_R_L = os.path.join(ASSET_PATH, "drive_right_left_eye.png")
    RACING_TURN_R_R = os.path.join(ASSET_PATH, "drive_right_right_eye.png")
    RACING_TURN_L_L = os.path.join(ASSET_PATH, "drive_left_left_eye.png")
    RACING_TURN_L_R = os.path.join(ASSET_PATH, "drive_left_right_eye.png")
    DOING_ACTION_L = os.path.join(ASSET_PATH, "doing_action_left.png")
    DOING_ACTION_R = os.path.join(ASSET_PATH, "doing_action_right.png")


class OledImage(Enum):
    """Enums for eye images.

    Users of Oled eyes can use these and let the Oled class decide which side
    to use.
    """

    DEFAULT_EYE = auto()
    BLINK = auto()
    ARUCO_DEF = auto()
    RACING_STRAIGHT = auto()
    RACING_TURN_R = auto()
    RACING_TURN_L = auto()
    DOING_ACTION = auto()


class TestAssets(Enum):
    LOADING_GIF = os.path.join(ASSET_PATH, "loading_balls_2.gif")
    LOGO = os.path.join(ASSET_PATH, "surrogatetv_logo.png")
