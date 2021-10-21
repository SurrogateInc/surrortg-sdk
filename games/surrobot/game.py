import argparse
import logging
import os

if os.getenv("MOCK_HW", False):
    from games.surrobot.mock_hw import MockArucoDetector as ArucoDetector
    from games.surrobot.mock_hw import MockHw as Hw
else:
    from games.surrobot.hw import Hw
    from surrortg.image_recognition.aruco import ArucoDetector

from games.surrobot.surrobot_config import ConfigParser, generate_configs
from games.surrobot.surrobot_inputs import generate_inputs
from games.surrobot.surrobot_templates import (
    CustomGame,
    ExplorationGame,
    ObjectHuntGame,
    RacingGame,
    StarterGame,
)
from surrortg import Game


class SurrobotGame(Game):
    async def on_init(self):
        self.templates = {
            "racing": RacingGame(self),
            "objectHunt": ObjectHuntGame(self),
            "exploration": ExplorationGame(self),
            "gettingStarted": StarterGame(self),
            "custom": CustomGame(self),
        }
        configs = generate_configs(self.templates, "gettingStarted")
        self.io.set_game_configs(configs)
        self.config_parser = ConfigParser(self)

        self.inputs = {}
        self.hw = Hw()

        self.hw.reset_eyes()
        self.aruco_source = await ArucoDetector.create(
            vertical_flip=True, horizontal_flip=True
        )
        self.template = None

    async def on_config(self):
        # Read game template
        # Default to "custom" if template id does not match to know
        # templates. This can happen for e.g. when robots with different
        # surrogate sdk versions connect to same GE
        # Note: The default template should not send scores
        # or otherwise affect the GE game loop
        new_template = self.templates["custom"]
        new_template_id = self.config_parser.current_template()
        if new_template_id in self.templates:
            new_template = self.templates[new_template_id]
        if self.template != new_template:
            # Cleanup old selection
            # Select the new template
            self.aruco_source.unregister_all_observers()
            self.template = new_template
            await self.template.on_template_selected()
        logging.info(f"Game template: {type(self.template).__name__}")

        if self.inputs:
            self.io.unregister_inputs(list(self.inputs.keys()))
        self.inputs = generate_inputs(
            self.hw, self.config_parser, self.template.input_callback
        )
        self.io.register_inputs(self.inputs)
        overlay = self.template.custom_overlay()
        self.io.set_custom_overlay(overlay)

        await self.template.on_config()

    async def on_start(self):
        logging.info("Game starts")
        await self.template.on_start()

    async def on_finish(self):
        logging.info("Game ends")
        # If reset during previous game self.template might not exist
        if self.template is not None:
            await self.template.on_finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Surrobot Game")
    parser.add_argument(
        "-c",
        "--conf",
        metavar="",
        help="path to configuration .toml file",
        required=False,
    )
    args = parser.parse_args()
    if args.conf is not None:
        SurrobotGame().run(config_path=args.conf)
    else:
        SurrobotGame().run()
