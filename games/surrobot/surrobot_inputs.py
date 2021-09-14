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

class ServoRotateButton(Switch):
    def __init__(self, servo, speed, defaults=None):
        super().__init__(defaults)
        self.servo = servo
        self.speed = speed

    async def off(self, seat=0):
        self.servo.rotation_speed = 0

    async def on(self, seat=0):
        self.servo.rotation_speed = self.speed


def generate_inputs(hw, config_parser):
    inputs = {}

    movement_slot = config_parser.get_slot_config(Slot.MOVEMENT)
    joystick_size = 20
    actuator_size = 15
    button_size = 15
    small_button_size = 10
    if movement_slot in [Extension.DRIVE_4_WHEELS, Extension.DRIVE_2_WHEELS]:
        # TODO: Set the motor_controller to some 4 or 2 wheel mode
        motor_joystick = MotorJoystick(
            hw.motor_controller,
            defaults={
                "humanReadableName": "movement",
                "onScreenPosition": on_screen_position(10, 80, joystick_size),
                "xMinKeys": keys_object("left", [KeyCode.KEY_A]),
                "xMaxKeys": keys_object("right", [KeyCode.KEY_D]),
                "yMinKeys": keys_object("back", [KeyCode.KEY_S]),
                "yMaxKeys": keys_object("forward", [KeyCode.KEY_W]),
            },
        )
        inputs["movement"] = motor_joystick
    elif movement_slot is Extension.SEPARATE_MOTORS:
        motors = [hw.motor_fl, hw.motor_fr, hw.motor_rr, hw.motor_rl]
        keys = [[KeyCode.KEY_Q, KeyCode.KEY_W], [KeyCode.KEY_A, KeyCode.KEY_S], [KeyCode.KEY_E, KeyCode.KEY_R], [KeyCode.KEY_D, KeyCode.KEY_F]]
        positions = [[10, 92],[25, 92],[10, 80],[25, 80]]
        for i, motor in enumerate(motors):
            motor_actuator = MotorActuator(
                motor,
                defaults={
                    "humanReadableName": f"Motor {i}",
                    "onScreenPosition": on_screen_position(positions[i][0], positions[i][1], actuator_size),
                    "minKeys": keys_object("reverse", [keys[i][0]]),
                    "maxKeys": keys_object("forward", [keys[i][1]]),
                },
            )
            inputs[f"motor{i}"] = motor_actuator

    top_front_slot = config_parser.get_slot_config(Slot.TOP_FRONT)
    top_front_servos = hw.servos[:3]
    if top_front_slot is Extension.CAMERA_2_AXIS:
        camera = ServoJoystick(
            top_front_servos[0],
            top_front_servos[1],
            defaults={
                "humanReadableName": "look",
                "onScreenPosition": on_screen_position(90, 80, joystick_size),
                "xMinKeys": keys_object("left", [KeyCode.KEY_ARROW_LEFT]),
                "xMaxKeys": keys_object("right", [KeyCode.KEY_ARROW_RIGHT]),
                "yMinKeys": keys_object("down", [KeyCode.KEY_ARROW_DOWN]),
                "yMaxKeys": keys_object("up", [KeyCode.KEY_ARROW_UP]),
            },
        )
        inputs["camera2Axis"] = camera
    
    top_back_slot = config_parser.get_slot_config(Slot.TOP_BACK)
    top_back_servos = hw.servos[3:7]
    top_back_keys = [[KeyCode.KEY_Y, KeyCode.KEY_U], [KeyCode.KEY_H, KeyCode.KEY_J], [KeyCode.KEY_I, KeyCode.KEY_O], [KeyCode.KEY_K, KeyCode.KEY_F]]
    if top_back_slot is Extension.ROBOT_ARM:
        pivots = ["shoulder", "elbow", "wrist"]
        for i, pivot in enumerate(pivots): 
            pivotActuator = ServoActuator(
                top_back_servos[0],
                defaults={
                    "humanReadableName": "shoulder",
                    "onScreenPosition": on_screen_position(10, 10 + (i*7), actuator_size),
                    "minKeys": keys_object("min", [top_back_keys[i][0]]),
                    "maxKeys": keys_object("max", [top_back_keys[i][0]]),
                },
            )
            inputs[f"robotArm{pivot.capitalize()}"] = pivotActuator
    elif top_back_slot is Extension.BUTTON_PRESSER:
        for i, servo in enumerate(top_back_servos): 
            presser = ServoButton(
                servo,
                defaults={
                    "humanReadableName": f"top button {i}",
                    "onScreenPosition": on_screen_position(10, 10+(i*14), small_button_size),
                    "keys": [top_back_keys[i][0]],
                },
            )
            inputs[f"topBackButtonPresser{i}"] = presser
    if top_back_slot is Extension.KNOB_TURNER:
        for i, servo in enumerate(top_back_servos): 
            turner = ServoActuator(
                servo,
                defaults={
                    "humanReadableName": "top knob turner {i}",
                    "onScreenPosition": on_screen_position(10, 10+(i*14), small_button_size),
                    "minKeys": keys_object("close", [top_back_keys[i][0]]),
                    "maxKeys": keys_object("open", [top_back_keys[i][1]]),
                },
            )
            inputs[f"toBackKnobTurner{i}"] = turner
    if top_back_slot is Extension.SWITCH_FLICKER:
        for i, servo in enumerate(top_back_servos): 
            directions = ["off", "on"]
            positions = [-1, 1]
            for i_direction, direction in enumerate(directions): 
                button = ServoButton(
                    servo,
                    on_position=positions[i_direction],
                    off_position=positions[i_direction],
                    defaults={
                        "humanReadableName": f"top flicker {i} {direction}",
                        "onScreenPosition": on_screen_position(10 + (i_direction*10), 10+(i*14), small_button_size),
                        "keys": [top_back_keys[i][i_direction]],
                    },
                )
                inputs[f"topBackFlicker{i}{direction.capitalize()}"] = button

    bottom_front_slot = config_parser.get_slot_config(Slot.BOTTOM_FRONT)
    bottom_front_servo = hw.servos[7]
    bottom_front_keys = [KeyCode.KEY_N, KeyCode.KEY_M]
    if bottom_front_slot is Extension.CLAW:
        directions = ["close", "open"]
        speeds = [-0.5, 0.5]
        for i, direction in enumerate(directions): 
            speedButton = ServoRotateButton(
                bottom_front_servo,
                speeds[i],
                defaults={
                    "humanReadableName": f"claw {direction}",
                    "onScreenPosition": on_screen_position(42 + (i*16), 85, button_size),
                    "keys": [bottom_front_keys[i]],
                },
            )
            inputs[f"bottomFrontClaw{direction.capitalize()}"] = speedButton
    elif bottom_front_slot is Extension.BUTTON_PRESSER:
        presser = ServoButton(
            bottom_front_servo,
            defaults={
                "humanReadableName": "button",
                "onScreenPosition": on_screen_position(50, 85, button_size),
                "keys": [bottom_front_keys[0]],
            },
        )
        inputs["bottomFrontButtonPresser"] = presser
    if bottom_front_slot is Extension.KNOB_TURNER:
        turner = ServoActuator(
            bottom_front_servo,
            defaults={
                "humanReadableName": "knob turner",
                "onScreenPosition": on_screen_position(50, 85, actuator_size),
                "minKeys": keys_object("close", [bottom_front_keys[0]]),
                "maxKeys": keys_object("open", [bottom_front_keys[1]]),
            },
        )
        inputs["bottomFrontKnobTurner"] = turner
    if bottom_front_slot is Extension.SWITCH_FLICKER:
        directions = ["off", "on"]
        positions = [-1, 1]
        for i, direction in enumerate(directions): 
            button = ServoButton(
                bottom_front_servo,
                on_position=positions[i],
                off_position=positions[i],
                defaults={
                    "humanReadableName": f"flicker {direction}",
                    "onScreenPosition": on_screen_position(42 + (i*16), 85, button_size),
                    "keys": [bottom_front_keys[i]],
                },
            )
            inputs[f"bottomFrontFlicker{direction.capitalize()}"] = button

    return inputs
