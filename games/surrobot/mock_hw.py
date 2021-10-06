import asyncio
import logging
import random
from enum import Enum, auto

SERVO_PINS = [17, 27, 22, 25, 24, 23, 5, 18]


# TODO: figure out how to get rid of this mock
class MockOledImage(Enum):
    DEFAULT_EYE = auto()
    BLINK = auto()
    ARUCO_DEF = auto()
    RACING_STRAIGHT = auto()
    RACING_TURN_R = auto()
    RACING_TURN_L = auto()
    DOING_ACTION = auto()


class BaseMock:
    def __init__(self, attrs={}):
        self._attrs = attrs

    def __setattr__(self, name, value):
        if name == "_attrs":
            super().__setattr__(name, value)
            return
        attrs = self.__getattribute__("_attrs")
        if name in attrs:
            logging.info(f"{self.__class__} setting {name} to: {value}")
            attrs[name] = value
            return
        super().__setattr__(name, value)

    def __getattr__(self, name):
        attrs = self.__getattribute__("_attrs")
        if name in attrs:
            return attrs[name]
        return super().__getattr__(name)


class MockServo(BaseMock):
    def __init__(self, pin):
        super().__init__({"rotation_speed": 0})
        self.pin = pin

    async def rotate_to(self, position, rotation_speed=None):
        logging.info(f"Moving servo {self.pin} to position: {position}")


class MockLedMatrix(BaseMock):
    def enable(self):
        logging.info("Led matrix enabled")

    def disable(self):
        logging.info("Led matrix disabled")

    def show_image(self, image):
        logging.info("Showing image on led matrix")


class MockOled(BaseMock):
    def show_text(self, txt):
        logging.info(f"Writing text to eye: {txt}")

    def show_image(self, image):
        logging.info("Showing image on eye")

    def show_default_image(self, image):
        logging.info("Showing default image on eye")

    def clear(self):
        logging.info("Clearing eye")


class MockColorSensor(BaseMock):
    def __init__(self):
        super().__init__(
            {
                "lux": 10,
            }
        )


class MockMotor(BaseMock):
    def __init__(self, name):
        super().__init__(
            {
                "speed": 0,
            }
        )


class MockMotorController(BaseMock):
    def __init__(self):
        super().__init__(
            {
                "longitudinal_speed": 0,
                "rotational_speed": 0,
            }
        )


class MockArucoDetector(BaseMock):
    @classmethod
    async def create(*args, **kwargs):
        return MockArucoDetector()

    def unregister_all_observers(self):
        return


class MockArucoMarker:
    def __init__(self, id, corners, resolution):
        self.id = id
        self.corners = corners
        self.resolution = resolution


class MockArucoFilter:
    def __init__(self, callback, aruco_source, ids=[], *args, **kwargs):
        super().__init__()
        self.callback = callback
        self.ids = ids
        self.callback_task = None

    async def callback_loop(self):
        while True:
            await asyncio.sleep(10)
            if self.ids:
                id = random.choice(self.ids)
                marker = MockArucoMarker(id, None, None)
                logging.info(f"MockArucoFilter callback for id: {id}")
                self.callback(marker)

    def start(self, *args, **kwargs):
        logging.info("MockArucoFilter - start")
        self.stop()
        self.callback_task = asyncio.create_task(self.callback_loop())

    def stop(self, *args, **kwargs):
        logging.info("MockArucoFilter - stop")
        if self.callback_task:
            self.callback_task.cancel()


class MockHw(BaseMock):
    def __init__(self):
        super().__init__()
        self.servos = [MockServo(pin) for pin in SERVO_PINS]
        self.left_eye = MockOled()
        self.right_eye = MockOled()
        self.color_sensor = MockColorSensor()
        self.motor_fl = MockMotor("fl")
        self.motor_fr = MockMotor("fr")
        self.motor_rr = MockMotor("rr")
        self.motor_rl = MockMotor("rl")
        self.motor_controller = MockMotorController()
        self.led_matrix = MockLedMatrix()

    def reset_eyes(self):
        self.def_img_to_eyes(MockOledImage.BLINK)

    # TODO: better name
    def def_img_to_eyes(self, img_enum):
        self.left_eye.show_default_image(img_enum)
        self.right_eye.show_default_image(img_enum)

    def get_cpu_temperature(self):
        return 0
