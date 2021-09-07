from games.surrobot.surrobot_config import Extension, Slot
from surrortg.inputs import (
    Joystick,
    KeyCode,
    LinearActuator,
    Switch,
    keys_object,
    on_screen_position,
)


class MotorJoystick(Joystick):
    def __init__(self, motor_controller, defaults=None):
        super().__init__(defaults)
        self.motor_controller = motor_controller

    async def handle_coordinates(self, x, y, seat=0):
        self.motor_controller.rotational_speed = x
        self.motor_controller.longitudinal_speed = y


class ServoJoystick(Joystick):
    def __init__(self, servo_x, servo_y=None, defaults=None):
        super().__init__(defaults)
        self.servo_x = servo_x
        self.servo_y = servo_y

    async def handle_coordinates(self, x, y, seat=0):
        self.servo_x.rotation_speed = x
        if self.servo_y:
            self.servo_y.rotation_speed = y


class ServoActuator(LinearActuator):
    def __init__(self, servo, defaults=None):
        super().__init__(defaults)
        self.servo = servo

    async def drive_actuator(self, val, seat=0):
        self.servo.rotation_speed = val


class ServoButton(Switch):
    def __init__(self, servo, on_position=1, off_position=-1, defaults=None):
        super().__init__(defaults)
        self.servo = servo
        self.on_position = on_position
        self.off_position = off_position

    async def off(self, seat=0):
        await self.servo.rotate_to(self.off_position)

    async def on(self, seat=0):
        await self.servo.rotate_to(self.on_position)


def generate_inputs(hw, config_parser):
    inputs = {}

    movement_slot = config_parser.get_slot_config(Slot.MOVEMENT)
    if movement_slot in [Extension.DRIVE_4_WHEELS, Extension.DRIVE_2_WHEELS]:
        # TODO: Set the motor_controller to some 4 or 2 wheel mode
        motor_joystick = MotorJoystick(
            hw.motor_controller,
            defaults={
                "humanReadableName": "movement",
                "onScreenPosition": on_screen_position(20, 80, 20),
                "xMinKeys": keys_object("left", [KeyCode.KEY_A]),
                "xMaxKeys": keys_object("right", [KeyCode.KEY_D]),
                "yMinKeys": keys_object("back", [KeyCode.KEY_S]),
                "yMaxKeys": keys_object("forward", [KeyCode.KEY_W]),
            },
        )
        inputs["movement"] = motor_joystick

    top_front_slot = config_parser.get_slot_config(Slot.TOP_FRONT)
    if top_front_slot is Extension.CAMERA_2_AXIS:
        camera = ServoJoystick(
            hw.servos[0],
            hw.servos[1],
            defaults={
                "humanReadableName": "look",
                "onScreenPosition": on_screen_position(80, 80, 20),
                "xMinKeys": keys_object("left", [KeyCode.KEY_ARROW_LEFT]),
                "xMaxKeys": keys_object("right", [KeyCode.KEY_ARROW_RIGHT]),
                "yMinKeys": keys_object("down", [KeyCode.KEY_ARROW_DOWN]),
                "yMaxKeys": keys_object("up", [KeyCode.KEY_ARROW_UP]),
            },
        )
        inputs["topFrontCamera"] = camera

    bottom_front_slot = config_parser.get_slot_config(Slot.BOTTOM_FRONT)
    if bottom_front_slot is Extension.CLAW:
        claw = ServoActuator(
            hw.servos[4],
            defaults={
                "humanReadableName": "claw",
                "onScreenPosition": on_screen_position(50, 80, 20),
                "minKeys": keys_object("close", [KeyCode.KEY_N]),
                "maxKeys": keys_object("open", [KeyCode.KEY_M]),
            },
        )
        inputs["bottomFrontClaw"] = claw
    elif bottom_front_slot is Extension.BUTTON_PRESSER:
        presser = ServoButton(
            hw.servos[4],
            defaults={
                "humanReadableName": "button",
                "onScreenPosition": on_screen_position(50, 80, 20),
                "keys": [KeyCode.KEY_N],
            },
        )
        inputs["bottomFrontButtonPresser"] = presser

    return inputs
