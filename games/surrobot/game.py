import logging
import os

if os.getenv("MOCK_HW", False):
    from games.surrobot.mock_hw import MockArucoDetector as ArucoDetector
    from games.surrobot.mock_hw import MockHw as Hw
else:
    from games.surrobot.hw import Hw
    from surrortg.image_recognition.aruco import ArucoDetector

from games.surrobot.surrobot_config import ConfigParser, generate_configs
from games.surrobot.surrobot_templates import (
    ExplorationGame,
    ObjectHuntGame,
    RacingGame,
)
from surrortg import Game
from surrortg.inputs import Joystick, KeyCode, LinearActuator


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


class ServosActuator(ServoActuator):
    async def drive_actuator(self, val, seat=0):
        for servo in self.servo:
            servo.rotation_speed = val


class SurrobotGame(Game):
    async def on_init(self):
        self.templates = {
            "racing": RacingGame(self),
            "object-hunt": ObjectHuntGame(self),
            "custom": ExplorationGame(self),
        }
        configs = generate_configs(self.templates, "racing")
        self.io.set_game_configs(configs)
        self.config_parser = ConfigParser(self)

        self.inputs = {}
        self.hw = Hw()

        # Preferably the input configs could be "live reloaded" based on the
        # "slot" & etc configuration. For e.g movement slot selection
        # "4 wheel drive" & "2 wheel drive" would give create following
        # joystick with correct motor_controller (4 or 2 wheel)
        motor_joystick = MotorJoystick(
            self.hw.motor_controller,
            custom_binds=[
                {
                    "up": KeyCode.KEY_W,
                    "down": KeyCode.KEY_S,
                    "left": KeyCode.KEY_A,
                    "right": KeyCode.KEY_D,
                }
            ],
        )
        self.inputs["movement"] = motor_joystick

        camera = ServoJoystick(
            self.hw.servos[0],
            self.hw.servos[1],
            [
                {
                    "up": KeyCode.KEY_ARROW_UP,
                    "down": KeyCode.KEY_ARROW_DOWN,
                    "left": KeyCode.KEY_ARROW_LEFT,
                    "right": KeyCode.KEY_ARROW_RIGHT,
                }
            ],
        )
        self.inputs["top-slot-1-camera"] = camera

        claw = ServosActuator(
            self.hw.servos,
            [
                {
                    "min": "KeyN",
                    "max": "KeyM",
                }
            ],
        )
        self.inputs["bottom-slot-claw"] = claw

        self.io.register_inputs(self.inputs)
        self.hw.reset_eyes()
        self.aruco_source = await ArucoDetector.create()
        self.template = None

    async def on_config(self):
        # Read game template
        new_template = self.templates[self.config_parser.current_template()]
        if self.template != new_template:
            # Cleanup old selection
            self.aruco_source.unregister_all_observers()
            # Select the new template
            self.template = new_template
            await self.template.on_template_selected()
        logging.info(f"Game template: {type(self.template).__name__}")
        # Could we set inputs here based on the game template + slot config?
        await self.template.on_config()

    async def on_start(self):
        logging.info("Game starts")
        await self.template.on_start()

    async def on_finish(self):
        logging.info("Game ends")
        # if reset during previous game self.template might not exist
        if self.template is not None:
            await self.template.on_finish()


if __name__ == "__main__":
    # Start running the game
    SurrobotGame().run()
