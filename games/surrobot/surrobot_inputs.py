from games.surrobot.surrobot_config import Extension, Slot
from surrortg.inputs import Joystick, KeyCode, LinearActuator, Switch


class MotorJoystick(Joystick):
    def __init__(self, motor_controller, custom_binds=None):
        self.motor_controller = motor_controller
        self.custom_binds = custom_binds

    async def handle_coordinates(self, x, y, seat=0):
        self.motor_controller.rotational_speed = x
        self.motor_controller.longitudinal_speed = y

    def get_default_keybinds(self):
        if self.custom_binds:
            return self.custom_binds
        return super().get_default_keybinds()


class ServoJoystick(Joystick):
    def __init__(self, servo_x, servo_y=None, custom_binds=None):
        self.servo_x = servo_x
        self.servo_y = servo_y
        self.custom_binds = custom_binds

    async def handle_coordinates(self, x, y, seat=0):
        self.servo_x.rotation_speed = x
        if self.servo_y:
            self.servo_y.rotation_speed = y

    def get_default_keybinds(self):
        if self.custom_binds:
            return self.custom_binds
        return super().get_default_keybinds()


class ServoActuator(LinearActuator):
    def __init__(self, servo, custom_binds=None):
        self.servo = servo
        self.custom_binds = custom_binds

    async def drive_actuator(self, val, seat=0):
        self.servo.rotation_speed = val

    def get_default_keybinds(self):
        if self.custom_binds:
            return self.custom_binds
        return super().get_default_keybinds()


class ServoButton(Switch):
    def __init__(
        self, servo, on_position=1, off_position=-1, custom_binds=None
    ):
        self.servo = servo
        self.on_position = on_position
        self.off_position = off_position
        self.custom_binds = custom_binds

    async def off(self, seat=0):
        await self.servo.rotate_to(self.off_position)

    async def on(self, seat=0):
        await self.servo.rotate_to(self.on_position)

    def get_default_keybinds(self):
        if self.custom_binds:
            return self.custom_binds
        return super().get_default_keybinds()


def generate_inputs(hw, config_parser):
    inputs = {}

    movement_slot = config_parser.get_slot_config(Slot.MOVEMENT)
    if movement_slot in [Extension.DRIVE_4_WHEELS, Extension.DRIVE_2_WHEELS]:
        # TODO: Set the motor_controller to some 4 or 2 wheel mode
        motor_joystick = MotorJoystick(
            hw.motor_controller,
            custom_binds=[
                {
                    "up": KeyCode.KEY_W,
                    "down": KeyCode.KEY_S,
                    "left": KeyCode.KEY_A,
                    "right": KeyCode.KEY_D,
                }
            ],
        )
        inputs["movement"] = motor_joystick

    top_front_slot = config_parser.get_slot_config(Slot.TOP_FRONT)
    if top_front_slot is Extension.CAMERA_2_AXIS:
        camera = ServoJoystick(
            hw.servos[0],
            hw.servos[1],
            [
                {
                    "up": KeyCode.KEY_ARROW_UP,
                    "down": KeyCode.KEY_ARROW_DOWN,
                    "left": KeyCode.KEY_ARROW_LEFT,
                    "right": KeyCode.KEY_ARROW_RIGHT,
                }
            ],
        )
        inputs["topFrontCamera"] = camera

    bottom_front_slot = config_parser.get_slot_config(Slot.BOTTOM_FRONT)
    if bottom_front_slot is Extension.CLAW:
        claw = ServoActuator(
            hw.servos[4],
            [
                {
                    "min": "KeyN",
                    "max": "KeyM",
                }
            ],
        )
        inputs["bottomFrontClaw"] = claw
    elif bottom_front_slot is Extension.BUTTON_PRESSER:
        presser = ServoButton(hw.servos[4], custom_binds=["KeyN"])
        inputs["bottomFrontButtonPresser"] = presser

    return inputs
