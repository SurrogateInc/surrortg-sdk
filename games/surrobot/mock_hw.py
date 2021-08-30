SERVO_PINS = [21, 20, 16, 13, 12, 25]


class MockServo:
    def __init__(self, pin):
        self.pin = pin

    async def rotate_to(self, position, rotation_speed=None):
        print(f"Moving servo {self.pin} to position: {position}")


class MockOled:
    def show_text(self, txt):
        print(f"Writing text to eye: {txt}")

    def show_image(self, image):
        print("Showing image on eye")

    def clear(self):
        print("Clearing eye")


class MockColorSensor:
    def __init__(self):
        self.lux = 10


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


class MockHw:
    def __init__(self):
        self.servos = [MockServo(pin) for pin in SERVO_PINS]
        self.left_eye = MockOled()
        self.right_eye = MockOled()
        self.color_sensor = MockColorSensor()
        self.motor_controller = MockMotorController()

    def reset_eyes(self):
        self.left_eye.show_text("left eye")
        self.right_eye.show_text("right eye")

    def get_cpu_temperature(self):
        return 0
