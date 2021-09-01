from enum import Enum


class KeyCode(Enum):
    """
    These are the keycodes which work with Surrogate.tv. To check which key
    matches which keycode, see https://keycode.info/ on Chrome.
    """

    KEY_A = "KeyA"
    KEY_B = "KeyB"
    KEY_C = "KeyC"
    KEY_D = "KeyD"
    KEY_E = "KeyE"
    KEY_F = "KeyF"
    KEY_G = "KeyG"
    KEY_H = "KeyH"
    KEY_I = "KeyI"
    KEY_J = "KeyJ"
    KEY_K = "KeyK"
    KEY_L = "KeyL"
    KEY_M = "KeyM"
    KEY_N = "KeyN"
    KEY_O = "KeyO"
    KEY_P = "KeyP"
    KEY_Q = "KeyQ"
    KEY_R = "KeyR"
    KEY_S = "KeyS"
    KEY_T = "KeyT"
    KEY_U = "KeyU"
    KEY_V = "KeyV"
    KEY_W = "KeyW"
    KEY_X = "KeyX"
    KEY_Y = "KeyY"
    KEY_Z = "KeyZ"
    KEY_0 = "Digit0"
    KEY_1 = "Digit1"
    KEY_2 = "Digit2"
    KEY_3 = "Digit3"
    KEY_4 = "Digit4"
    KEY_5 = "Digit5"
    KEY_6 = "Digit6"
    KEY_7 = "Digit7"
    KEY_8 = "Digit8"
    KEY_9 = "Digit9"
    KEY_SHIFT_LEFT = "ShiftLeft"
    KEY_SHIFT_RIGHT = "ShiftRight"
    KEY_CTRL_LEFT = "ControlLeft"
    KEY_CTRL_RIGHT = "ControlRight"
    KEY_ALT_LEFT = "AltLeft"
    KEY_ALT_RIGHT = "AltRight"
    KEY_BACKQUOTE = "Backquote"
    KEY_MINUS = "Minus"
    KEY_EQUAL = "Equal"
    KEY_COMMA = "Comma"
    KEY_PERIOD = "Period"
    KEY_SLASH = "Slash"
    KEY_SEMICOLON = "Semicolon"
    KEY_QUOTE = "Quote"
    KEY_BACKSLASH = "Backslash"
    KEY_BRACKET_LEFT = "BracketLeft"
    KEY_BRACKET_RIGHT = "BracketRight"
    KEY_ARROW_UP = "ArrowUp"
    KEY_ARROW_DOWN = "ArrowDown"
    KEY_ARROW_LEFT = "ArrowLeft"
    KEY_ARROW_RIGHT = "ArrowRight"
    KEY_SPACE = "Space"


class InputOrientation(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


def assert_keycode_list(obj):
    assert isinstance(obj, list), "keycode list needs to be actual list"
    for keycode in obj:
        assert isinstance(
            keycode, KeyCode
        ), "non KeyCode entry in keycode list"


def assert_keys_object(obj):
    assert obj.keys() <= {
        "humanReadableName",
        "keys",
    }, "keys object with extra parameters"
    assert "keys" in obj, "keys list missing from keys object"
    assert_keycode_list(obj["keys"])
    assert "humanReadableName" in obj and isinstance(
        obj["humanReadableName"], str
    ), "humanReadableName must be a string"


def assert_on_screen_position(obj):
    assert isinstance(obj, dict), "onScreenPosition must be a dictionary"
    assert isinstance(
        "x" in obj and obj["x"], int
    ), "onScreenPosition.x must be integer"
    assert isinstance(
        "y" in obj and obj["y"], int
    ), "onScreenPosition.y must be integer"
    assert isinstance(
        "size" in obj and obj["size"], int
    ), "onScreenPosition.size must be integer"
    assert "orientation" not in obj or isinstance(
        obj["orientation"], InputOrientation
    ), "onScreenPosition.orientation not a InputOrientation enum"


def on_screen_position(x, y, size, orientation=None):
    obj = {
        "x": x,
        "y": y,
        "size": size,
    }
    if orientation:
        obj["orientation"] = orientation
    assert_on_screen_position(obj)
    return obj


def keys_object(name, keys):
    obj = {"humanReadableName": name, "keys": keys}
    assert_keys_object(obj)
    return obj


def value_if_enum(obj):
    if isinstance(obj, Enum):
        return obj.value
    return obj


# Helper function to convert enums in dict/list structure to values
def convert_enums_to_values(current):
    if isinstance(current, dict):
        output = {}
        for key, value in current.items():
            output[value_if_enum(key)] = convert_enums_to_values(value)
        return output
    if isinstance(current, list):
        return list(map(convert_enums_to_values, current))

    return value_if_enum(current)
