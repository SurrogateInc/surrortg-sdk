import pigpio

from games.claw.config import JOYSTICK_DISABLE_PIN


class ClawJoystickSplitter:
    def __init__(self, pi):
        self._pi = pi
        self._pi.set_mode(JOYSTICK_DISABLE_PIN, pigpio.OUTPUT)

        # Enable physical joystick by default
        self.enable_joystick()

    def enable_joystick(self):
        self._pi.write(JOYSTICK_DISABLE_PIN, 0)

    def disable_joystick(self):
        self._pi.write(JOYSTICK_DISABLE_PIN, 1)

    def close(self):
        self._pi.set_mode(JOYSTICK_DISABLE_PIN, pigpio.INPUT)
