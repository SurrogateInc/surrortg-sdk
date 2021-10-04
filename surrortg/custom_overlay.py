from enum import Enum


class Position(Enum):
    TOP_LEFT = "topLeft"
    TOP_RIGHT = "topRight"
    BOTTOM_LEFT = "bottomLeft"
    BOTTOM_RIGHT = "bottomRight"
    CENTER_LEFT = "centerLeft"
    CENTER_TOP = "centerTop"
    CENTER_RIGHT = "centerRight"
    CENTER_BOTTOM = "centerBottom"


class ElementType(Enum):
    PLAYER_LIST = "playerList"
    TIMER = "timer"
    STRING = "string"


class TimerType(Enum):
    REMAINING = "remaining"
    ELAPSED = "elapsed"


def overlay_config(elements, custom_elements={}):
    all_elements = elements.copy()
    for id, element in custom_elements.items():
        all_elements.append(
            {
                "type": element["type"],
                "position": element["defaultPosition"],
                "elementId": id,
            }
        )
    return {
        "elements": all_elements,
        "customElements": custom_elements,
        "modifiedByUser": False,
    }


def player_list(position=Position.TOP_LEFT):
    return {
        "type": ElementType.PLAYER_LIST.value,
        "position": position.value,
    }


def timer(timer_type=TimerType.REMAINING, position=Position.CENTER_TOP):
    return {
        "type": ElementType.TIMER.value,
        "timerType": timer_type.value,
        "position": position.value,
    }


def custom_text_element(name, position=Position.TOP_RIGHT, info_text=None):
    obj = {
        "type": ElementType.STRING.value,
        "defaultPosition": position.value,
        "displayName": name,
    }
    if info_text:
        obj["infoText"] = info_text
    return obj
