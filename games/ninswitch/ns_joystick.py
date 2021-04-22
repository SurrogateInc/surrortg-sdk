from surrortg.inputs import Joystick


class NSJoystick(Joystick):
    def __init__(self, x_axis, y_axis):
        self.x_axis = x_axis
        self.y_axis = y_axis

    async def handle_coordinates(self, x, y, seat=0):
        y = min(127, max(-128, int(y * -128))) + 128
        x = max(-128, min(127, int(x * 128))) + 128
        self.x_axis(x)
        self.y_axis(y)

    async def reset(self, seat=0):
        self.x_axis(128)
        self.y_axis(128)
