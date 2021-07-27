import logging

from games.surrobot.hw import Hw
from games.surrobot.template_games import Game1, Game3, RacingGame
from surrortg import ConfigType, Game
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


class SurrobotGame(Game):
    async def on_init(self):
        # Game Type Enum (Racing-Game, Free-Roam, Tag)
        # Different game types can have restriction to slot options? & offer
        # extra configuration spesific to game type.
        # Every game-type has it's own game loop
        # implementation. for e.g. racing-game requires 1 light sensor,
        # 4 wheel or 2 wheel drive
        # And the implementation will track lap times and send them to GE
        self.io.register_config(
            "game-template", ConfigType.INTEGER, 1, False, minimum=1, maximum=3
        )
        self.io.register_config(
            "game-template-2[conditional]-max-laps",
            ConfigType.INTEGER,
            3,
            False,
            minimum=1,
            maximum=10,
        )
        # Movement slot (side 4x motors, 4x servos)
        # Offer 4 wheel drive, 2 wheel drive etc
        self.io.register_config(
            "movement-slot", ConfigType.INTEGER, 1, False, minimum=1, maximum=4
        )
        self.io.register_config(
            "movement-speed",
            ConfigType.INTEGER,
            8,
            False,
            minimum=1,
            maximum=10,
        )
        # Top slot 1 (3x servos)
        # Offer servo arm, camera pivot, etc
        self.io.register_config(
            "top-slot-1", ConfigType.INTEGER, 1, False, minimum=1, maximum=4
        )
        # Bottom slot (1x servo)
        # Offer claw, button presser
        self.io.register_config(
            "bottom-slot", ConfigType.INTEGER, 1, False, minimum=1, maximum=2
        )

        self.inputs = {}
        self.hw = Hw()
        self.templates = [Game1(self.hw), RacingGame(self.hw), Game3(self.hw)]

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

        claw = ServoActuator(
            self.hw.servos[2],
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

    async def on_config(self):
        # Read game template
        game_template = self.configs["custom"]["game-template"]
        self.template = self.templates[game_template - 1]
        logging.info(f"game template: {game_template}")
        # Could we set inputs here based on the game template + slot config?

    async def on_start(self):
        logging.info("Game starts")
        score = await self.template.on_start()
        self.io.send_score(score=score, final_score=True)

    async def on_finish(self):
        logging.info("Game ends")
        # if reset during previous game self.template might not exist
        if hasattr(self, "template"):
            await self.template.on_finish()


if __name__ == "__main__":
    # Start running the game
    SurrobotGame().run()
