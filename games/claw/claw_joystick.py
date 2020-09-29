import logging
import pigpio
from surrortg.inputs import Joystick, Directions
from games.claw.config import (
    TOP_PIN,
    LEFT_PIN,
    BOTTOM_PIN,
    RIGHT_PIN,
    MIN_AMOUNT,
)

DIR_PINS = [TOP_PIN, LEFT_PIN, BOTTOM_PIN, RIGHT_PIN]

DIRECTION_CMD_MAP = {
    Directions.TOP: {
        "off": [TOP_PIN],
        "on": [BOTTOM_PIN, LEFT_PIN, RIGHT_PIN],
    },
    Directions.BOTTOM: {
        "off": [BOTTOM_PIN],
        "on": [TOP_PIN, LEFT_PIN, RIGHT_PIN],
    },
    Directions.LEFT: {
        "off": [LEFT_PIN],
        "on": [TOP_PIN, BOTTOM_PIN, RIGHT_PIN],
    },
    Directions.RIGHT: {
        "off": [RIGHT_PIN],
        "on": [TOP_PIN, BOTTOM_PIN, LEFT_PIN],
    },
    Directions.TOP_LEFT: {
        "off": [TOP_PIN, LEFT_PIN],
        "on": [BOTTOM_PIN, RIGHT_PIN],
    },
    Directions.TOP_RIGHT: {
        "off": [TOP_PIN, RIGHT_PIN],
        "on": [BOTTOM_PIN, LEFT_PIN],
    },
    Directions.BOTTOM_LEFT: {
        "off": [BOTTOM_PIN, LEFT_PIN],
        "on": [TOP_PIN, RIGHT_PIN],
    },
    Directions.BOTTOM_RIGHT: {
        "off": [BOTTOM_PIN, RIGHT_PIN],
        "on": [TOP_PIN, LEFT_PIN],
    },
    Directions.MIDDLE: {
        "off": [],
        "on": [TOP_PIN, BOTTOM_PIN, LEFT_PIN, RIGHT_PIN],
    },
}


class ClawJoystick(Joystick):
    def __init__(self, pi):
        super().__init__(min_amount=MIN_AMOUNT)
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
        GPIO_cmds = DIRECTION_CMD_MAP[direction]
        for off_pin in GPIO_cmds["off"]:
            self.pi.write(off_pin, 0)
        for on_pin in GPIO_cmds["on"]:
            self.pi.write(on_pin, 1)

    async def reset(self, seat=0):
        self.move(Directions.MIDDLE)
