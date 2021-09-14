import logging

SERVO_PINS = [17, 27, 22, 25, 24, 23, 5, 18]


class MockServo:
    def __init__(self, pin):
        self.pin = pin
        self._rotation_speed = 0

    async def rotate_to(self, position, rotation_speed=None):
        logging.info(f"Moving servo {self.pin} to position: {position}")
    
    @property
    def rotation_speed(self):
        return self._rotation_speed

    @rotation_speed.setter
    def rotation_speed(self, rotation_speed):
        logging.info(f"Rotation speed of {self.pin} to: {rotation_speed}")
        self._rotation_speed = rotation_speed


class MockOled:
    def show_text(self, txt):
        logging.info(f"Writing text to eye: {txt}")

    def show_image(self, image):
        logging.info("Showing image on eye")

    def clear(self):
        logging.info("Clearing eye")


class MockColorSensor:
    def __init__(self):
        self.lux = 10

class MockMotor:
    def __init__(self, name):
        self.name = name
        self._speed = 0
    
    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, speed):
        logging.info(f"Change speed of {self.name} to: {speed}")
        self._speed = speed


class MockMotorController:
    def __init__(self):
        self.rotational_speed = 0
        self.longitudinal_speed = 0
        

class MockArucoDetector:
    @classmethod
    async def create(*args, **kwargs):
        return MockArucoDetector()

    def unregister_all_observers(self):
        return


class MockArucoFilter:
    def __init__(*args, **kwargs):
        return
    
    def start(*args, **kwargs):
        logging.info("MockArucoFilter - start")
    
    def stop(*args, **kwargs):
        logging.info("MockArucoFilter - start")


class MockHw:
    def __init__(self):
        self.servos = [MockServo(pin) for pin in SERVO_PINS]
        self.left_eye = MockOled()
        self.right_eye = MockOled()
        self.color_sensor = MockColorSensor()
        self.motor_fl = MockMotor("fl")
        self.motor_fr = MockMotor("fr")
        self.motor_rr = MockMotor("rr")
        self.motor_rl = MockMotor("rl")
        self.motor_controller = MockMotorController()

    def reset_eyes(self):
        self.left_eye.show_text("left eye")
        self.right_eye.show_text("right eye")

    def get_cpu_temperature(self):
        return 0
