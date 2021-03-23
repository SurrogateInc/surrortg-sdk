import argparse
import logging

from surrortg import Game, RobotType


class OBSSceneSwitcher:
    """Changes OBS scenes

    This class changes OBS scenes using AdvancedSceneSwitcher.
    """

    def __init__(self, file_path):
        """Creates a OBS scene switcher with certain scene file path.

        :param file_path: path to scene file. Same path has to be configured
            to OBS.
        :type file_path: str
        """
        self.file_path = file_path

    def switch_scene(self, scene):
        """Switch scene based on scene name

        :param scene: scene name as written in OBS
        :type scene: str
        """

        with open(self.file_path, "w") as file:
            file.write(scene)
        logging.info(f"Scene changed to '{scene}'")


if __name__ == "__main__":

    class SceneSwitcherGame(Game):
        async def on_init(self):
            self.scene_switcher = OBSSceneSwitcher("./tmp.txt")
            self.scene_switcher.switch_scene("waiting")

        async def on_start(self):
            self.scene_switcher.switch_scene("game")

        async def on_finish(self):
            self.scene_switcher.switch_scene("waiting")

    parser = argparse.ArgumentParser("Simple OBS scene switcher")
    parser.add_argument(
        "-c",
        "--conf",
        metavar="",
        help="Path to configuration .toml file",
        required=False,
        default="/etc/srtg/srtg.toml",
    )
    parser.add_argument(
        "-d",
        "--device-id",
        metavar="",
        help="Device id to use when connecting",
        required=False,
        default=None,
    )

    args = parser.parse_args()
    SceneSwitcherGame().run(
        config_path=args.conf,
        robot_type=RobotType.LOGICAL,
        device_id=args.device_id,
    )
