import unittest

from surrortg.inputs import Directions, Joystick


class TestJoystick(Joystick):
    async def reset(self, seat):
        pass


class JoystickTest(unittest.TestCase):
    def test_get_direction_4(self):
        """Test that the directions are correct in 4 case"""
        joystick = TestJoystick()

        self.assertEqual(joystick.get_direction_4(0, 1), Directions.TOP)
        self.assertEqual(joystick.get_direction_4(0, -1), Directions.BOTTOM)
        self.assertEqual(joystick.get_direction_4(1, 0), Directions.RIGHT)
        self.assertEqual(joystick.get_direction_4(-1, 0), Directions.LEFT)

        self.assertEqual(joystick.get_direction_4(0, 0), Directions.MIDDLE)
        self.assertEqual(joystick.get_direction_4(0, 0.09), Directions.MIDDLE)

    def test_get_direction_8(self):
        """Test that the directions are correct in 8 case"""
        joystick = TestJoystick()

        self.assertEqual(joystick.get_direction_8(0, 1), Directions.TOP)
        self.assertEqual(joystick.get_direction_8(0, -1), Directions.BOTTOM)
        self.assertEqual(joystick.get_direction_8(1, 0), Directions.RIGHT)
        self.assertEqual(joystick.get_direction_8(-1, 0), Directions.LEFT)

        self.assertEqual(joystick.get_direction_8(0, 0), Directions.MIDDLE)
        self.assertEqual(joystick.get_direction_8(0, 0.09), Directions.MIDDLE)

        self.assertEqual(joystick.get_direction_8(-1, 1), Directions.TOP_LEFT)
        self.assertEqual(joystick.get_direction_8(1, 1), Directions.TOP_RIGHT)
        self.assertEqual(
            joystick.get_direction_8(-1, -1), Directions.BOTTOM_LEFT
        )
        self.assertEqual(
            joystick.get_direction_8(1, -1), Directions.BOTTOM_RIGHT
        )
