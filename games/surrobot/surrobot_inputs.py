from games.surrobot.surrobot_config import Extension, Slot
from surrortg.inputs import (
    Joystick,
    KeyCode,
    LinearActuator,
    Switch,
    keys_object,
    on_screen_position,
)

JOYSTICK_SIZE = 20
ACTUATOR_SIZE = 15
BUTTON_SIZE = 15
SMALL_BUTTON_SIZE = 10


class MotorJoystick(Joystick):
    def __init__(self, motor_controller, defaults=None):
        super().__init__(defaults)
        self.motor_controller = motor_controller

    async def handle_coordinates(self, x, y, seat=0):
        self.motor_controller.rotational_speed = x
        self.motor_controller.longitudinal_speed = y


class MotorActuator(LinearActuator):
    def __init__(self, motor, defaults=None):
        super().__init__(defaults)
        self.motor = motor

    async def drive_actuator(self, val, seat=0):
        self.motor.speed = val


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


class BidirectionalServoTurner(Switch):
    """Moves servo to either direction at constant speed

    Note: The direction of movement can be defined by using negative
    or positive speed.
    """

    def __init__(self, servo, speed, defaults=None):
        super().__init__(defaults)
        self.servo = servo
        self.speed = speed

    async def off(self, seat=0):
        self.servo.rotation_speed = 0

    async def on(self, seat=0):
        self.servo.rotation_speed = self.speed


class ButtonPositioner:
    def __init__(self, start_x, start_y, direction, padding):
        self.x = int(start_x)
        self.y = int(start_y)
        self.direction = direction
        self.padding = padding
        self.last_size = 0

    def next_place(self, size, custom_reserve_size=None):
        x_change = self.direction[0]
        y_change = self.direction[1]
        reserve = size
        if custom_reserve_size:
            reserve = custom_reserve_size
        if self.last_size != 0:
            self.x = int(
                self.x
                + x_change * self.last_size / 2
                + x_change * reserve / 2
                + x_change * self.padding
            )
            self.y = int(
                self.y
                + y_change * self.last_size / 2
                + y_change * reserve / 2
                + y_change * self.padding
            )
        self.last_size = reserve
        return on_screen_position(self.x, self.y, size)


def generate_movement_slot(hw, extension, custom, inputs):
    if extension in [Extension.DRIVE_4_WHEELS, Extension.DRIVE_2_WHEELS]:
        # TODO: Set the motor_controller to some 4 or 2 wheel mode
        motor_joystick = MotorJoystick(
            hw.motor_controller,
            defaults={
                "humanReadableName": "movement",
                "onScreenPosition": on_screen_position(10, 85, JOYSTICK_SIZE),
                "xMinKeys": keys_object("left", [KeyCode.KEY_A]),
                "xMaxKeys": keys_object("right", [KeyCode.KEY_D]),
                "yMinKeys": keys_object("back", [KeyCode.KEY_S]),
                "yMaxKeys": keys_object("forward", [KeyCode.KEY_W]),
            },
        )
        inputs["movement"] = motor_joystick
    elif extension is Extension.CUSTOM:
        motors = [hw.motor_fl, hw.motor_fr, hw.motor_rr, hw.motor_rl]
        binds = [
            [KeyCode.KEY_Q, KeyCode.KEY_W],
            [KeyCode.KEY_A, KeyCode.KEY_S],
            [KeyCode.KEY_E, KeyCode.KEY_R],
            [KeyCode.KEY_D, KeyCode.KEY_F],
        ]
        positions = [[10, 92], [25, 92], [10, 80], [25, 80]]
        for i, extension in enumerate(custom):
            if extension is Extension.SEPARATE_MOTOR:
                motor_actuator = MotorActuator(
                    motors[i],
                    defaults={
                        "humanReadableName": f"Motor {i}",
                        "onScreenPosition": on_screen_position(
                            positions[i][0], positions[i][1], ACTUATOR_SIZE
                        ),
                        "minKeys": keys_object("reverse", [binds[i][0]]),
                        "maxKeys": keys_object("forward", [binds[i][1]]),
                    },
                )
                inputs[f"seperateMotor{i}"] = motor_actuator


def generate_servo_extensions(
    slot, extensions, servos, inputs, binds, positioner
):
    for i, extension in enumerate(extensions):
        if extension is Extension.BUTTON_PRESSER:
            presser = ServoButton(
                servos[i],
                defaults={
                    "humanReadableName": "button",
                    "onScreenPosition": positioner.next_place(
                        SMALL_BUTTON_SIZE
                    ),
                    "keys": [binds[i][0]],
                },
            )
            inputs[f"{slot}ButtonPresser{i}"] = presser
        elif extension is Extension.KNOB_TURNER:
            turner = ServoActuator(
                servos[i],
                defaults={
                    "humanReadableName": "knob turner",
                    "onScreenPosition": positioner.next_place(
                        int(ACTUATOR_SIZE), SMALL_BUTTON_SIZE
                    ),
                    "minKeys": keys_object("close", [binds[i][0]]),
                    "maxKeys": keys_object("open", [binds[i][1]]),
                },
            )
            inputs[f"{slot}KnobTurner{i}"] = turner
        elif extension is Extension.SWITCH_FLICKER:
            directions = ["off", "on"]
            servo_positions = [-1, 1]
            mobile_position = positioner.next_place(SMALL_BUTTON_SIZE)
            for n, direction in enumerate(directions):
                button = ServoButton(
                    servos[i],
                    on_position=servo_positions[n],
                    off_position=servo_positions[n],
                    defaults={
                        "humanReadableName": f"flicker {direction}",
                        "onScreenPosition": on_screen_position(
                            int(
                                mobile_position["x"]
                                + ((n * 2 - 1) * SMALL_BUTTON_SIZE / 2)
                            ),
                            mobile_position["y"],
                            SMALL_BUTTON_SIZE,
                        ),
                        "keys": [binds[i][0]],
                    },
                )
                inputs[f"{slot}Flicker{i}{direction.capitalize()}"] = button


def generate_top_front_slot(hw, extension, custom, inputs):
    top_front_servos = hw.servos[:4]
    if extension is Extension.CAMERA_2_AXIS:
        camera = ServoJoystick(
            top_front_servos[1],
            top_front_servos[2],
            defaults={
                "humanReadableName": "look",
                "onScreenPosition": on_screen_position(90, 85, JOYSTICK_SIZE),
                "xMinKeys": keys_object("left", [KeyCode.KEY_ARROW_LEFT]),
                "xMaxKeys": keys_object("right", [KeyCode.KEY_ARROW_RIGHT]),
                "yMinKeys": keys_object("down", [KeyCode.KEY_ARROW_DOWN]),
                "yMaxKeys": keys_object("up", [KeyCode.KEY_ARROW_UP]),
            },
        )
        inputs["camera2Axis"] = camera
    elif extension is Extension.CUSTOM:
        positioner = ButtonPositioner(90, 85, (0, -1.5), 2)
        binds = [
            [KeyCode.KEY_ARROW_LEFT, KeyCode.KEY_ARROW_RIGHT],
            [KeyCode.KEY_ARROW_DOWN, KeyCode.KEY_ARROW_UP],
            [KeyCode.KEY_C, KeyCode.KEY_V],
            [KeyCode.KEY_Z, KeyCode.KEY_X],
        ]
        generate_servo_extensions(
            Slot.TOP_FRONT.value,
            custom,
            top_front_servos,
            inputs,
            binds,
            positioner,
        )


def generate_top_back_slot(hw, extension, custom, inputs):
    top_back_servos = hw.servos[4:7]
    top_back_keys = [
        [KeyCode.KEY_Y, KeyCode.KEY_U],
        [KeyCode.KEY_H, KeyCode.KEY_J],
        [KeyCode.KEY_I, KeyCode.KEY_O],
    ]
    if extension is Extension.ROBOT_ARM:
        pivots = ["shoulder", "elbow", "wrist"]
        for i, pivot in enumerate(pivots):
            pivot_actuator = ServoActuator(
                top_back_servos[i],
                defaults={
                    "humanReadableName": pivot,
                    "onScreenPosition": on_screen_position(
                        10, 10 + (i * 7), ACTUATOR_SIZE
                    ),
                    "minKeys": keys_object("min", [top_back_keys[i][0]]),
                    "maxKeys": keys_object("max", [top_back_keys[i][1]]),
                },
            )
            inputs[f"robotArm{pivot.capitalize()}"] = pivot_actuator
        return
    positioner = ButtonPositioner(10, 10, (0, 1.5), 2)
    if extension in [
        Extension.BUTTON_PRESSER,
        Extension.KNOB_TURNER,
        Extension.SWITCH_FLICKER,
    ]:
        generate_servo_extensions(
            Slot.TOP_BACK.value,
            [extension] * 4,
            top_back_servos,
            inputs,
            top_back_keys,
            positioner,
        )
    elif extension is Extension.CUSTOM:
        generate_servo_extensions(
            Slot.TOP_BACK.value,
            custom,
            top_back_servos,
            inputs,
            top_back_keys,
            positioner,
        )


def generate_bottom_front_slot(hw, extension, inputs):
    bottom_front_servo = hw.servos[7]
    binds = [KeyCode.KEY_N, KeyCode.KEY_M]
    if extension is Extension.CLAW:
        directions = ["close", "open"]
        speeds = [-0.5, 0.5]
        for i, direction in enumerate(directions):
            speed_button = BidirectionalServoTurner(
                bottom_front_servo,
                speeds[i],
                defaults={
                    "humanReadableName": f"claw {direction}",
                    "onScreenPosition": on_screen_position(
                        50 - int(BUTTON_SIZE / 2) + ((BUTTON_SIZE + 2) * i),
                        85,
                        BUTTON_SIZE,
                    ),
                    "keys": [binds[i]],
                },
            )
            inputs[f"bottomFrontClaw{direction.capitalize()}"] = speed_button
    elif extension in [
        Extension.BUTTON_PRESSER,
        Extension.KNOB_TURNER,
        Extension.SWITCH_FLICKER,
    ]:
        positioner = ButtonPositioner(50, 85, (0, 0), 0)
        generate_servo_extensions(
            Slot.BOTTOM_FRONT.value,
            [extension],
            [bottom_front_servo],
            inputs,
            [binds],
            positioner,
        )


def generate_inputs(hw, config_parser):
    inputs = {}

    movement_extension = config_parser.get_slot_config(Slot.MOVEMENT)
    movement_custom = config_parser.get_slot_custom_config(Slot.MOVEMENT)
    generate_movement_slot(hw, movement_extension, movement_custom, inputs)
    top_front_slot = config_parser.get_slot_config(Slot.TOP_FRONT)
    top_front_custom = config_parser.get_slot_custom_config(Slot.TOP_FRONT)
    generate_top_front_slot(hw, top_front_slot, top_front_custom, inputs)
    top_back_slot = config_parser.get_slot_config(Slot.TOP_BACK)
    top_back_custom = config_parser.get_slot_custom_config(Slot.TOP_BACK)
    generate_top_back_slot(hw, top_back_slot, top_back_custom, inputs)
    bottom_front_slot = config_parser.get_slot_config(Slot.BOTTOM_FRONT)
    generate_bottom_front_slot(hw, bottom_front_slot, inputs)

    return inputs
