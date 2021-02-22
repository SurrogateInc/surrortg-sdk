import logging
import pigpio
from surrortg.inputs import Joystick, Directions
from games.claw.config import (
    TOP_PIN,
    LEFT_PIN,
    BOTTOM_PIN,
    RIGHT_PIN,
    MIN_AMOUNT,
    JOYSTICK_STATE_ON,
    JOYSTICK_STATE_OFF,
)

DIR_PINS = [TOP_PIN, LEFT_PIN, BOTTOM_PIN, RIGHT_PIN]

DIRECTION_CMD_MAP = {
    Directions.TOP: {
        "on": [TOP_PIN],
        "off": [BOTTOM_PIN, LEFT_PIN, RIGHT_PIN],
    },
    Directions.BOTTOM: {
        "on": [BOTTOM_PIN],
        "off": [TOP_PIN, LEFT_PIN, RIGHT_PIN],
    },
    Directions.LEFT: {
        "on": [LEFT_PIN],
        "off": [TOP_PIN, BOTTOM_PIN, RIGHT_PIN],
    },
    Directions.RIGHT: {
        "on": [RIGHT_PIN],
        "off": [TOP_PIN, BOTTOM_PIN, LEFT_PIN],
    },
    Directions.TOP_LEFT: {
        "on": [TOP_PIN, LEFT_PIN],
        "off": [BOTTOM_PIN, RIGHT_PIN],
    },
    Directions.TOP_RIGHT: {
        "on": [TOP_PIN, RIGHT_PIN],
        "off": [BOTTOM_PIN, LEFT_PIN],
    },
    Directions.BOTTOM_LEFT: {
        "on": [BOTTOM_PIN, LEFT_PIN],
        "off": [TOP_PIN, RIGHT_PIN],
    },
    Directions.BOTTOM_RIGHT: {
        "on": [BOTTOM_PIN, RIGHT_PIN],
        "off": [TOP_PIN, LEFT_PIN],
    },
    Directions.MIDDLE: {
        "on": [],
        "off": [TOP_PIN, BOTTOM_PIN, LEFT_PIN, RIGHT_PIN],
    },
}


class ClawJoystick(Joystick):
    def __init__(self, pi):
        self.set_min_amount(MIN_AMOUNT)
        self.pi = pi
        # set out pins
        for dir_pin in DIR_PINS:
            self.pi.set_mode(dir_pin, pigpio.OUTPUT)
        # get into stopped state
        self.move(Directions.MIDDLE)

    async def handle_coordinates(self, x, y, seat=0):
        direction = self.get_direction_8(x, y)
        self.move(direction)

    def move(self, direction):
        logging.debug(f"Moving {direction}")
        gpio_cmds = DIRECTION_CMD_MAP[direction]
        for off_pin in gpio_cmds["off"]:
            self.pi.write(off_pin, JOYSTICK_STATE_OFF)
        for on_pin in gpio_cmds["on"]:
            self.pi.write(on_pin, JOYSTICK_STATE_ON)

    async def reset(self, seat=0):
        self.move(Directions.MIDDLE)
