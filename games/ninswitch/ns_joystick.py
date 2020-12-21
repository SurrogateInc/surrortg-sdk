from surrortg.inputs import Joystick, Directions

DIRECTION_TO_JOYSTICK_VALS = {
    Directions.TOP: (128, 0),
    Directions.BOTTOM: (128, 255),
    Directions.LEFT: (0, 128),
    Directions.RIGHT: (255, 128),
    Directions.TOP_LEFT: (0, 0),
    Directions.TOP_RIGHT: (255, 0),
    Directions.BOTTOM_LEFT: (0, 255),
    Directions.BOTTOM_RIGHT: (255, 255),
    Directions.MIDDLE: (128, 128),
}


class NSJoystick(Joystick):
    def __init__(self, x_axis, y_axis):
        self.x_axis = x_axis
        self.y_axis = y_axis

    async def handle_coordinates(self, x, y, seat=0):
        direction = self.get_direction_8(x, y)
        x, y = DIRECTION_TO_JOYSTICK_VALS[direction]
        self.x_axis(x)
        self.y_axis(y)

    async def reset(self, seat=0):
        self.x_axis(128)
        self.y_axis(128)
