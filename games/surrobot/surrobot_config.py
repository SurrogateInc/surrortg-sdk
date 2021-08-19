from enum import Enum

from surrortg.game_io import ConfigType


class Slot(Enum):
    TOP_FRONT = "top-front"
    TOP_BACK = "top-back"
    BOTTOM_FRONT = "bottom-front"
    BOTTOM_SENSOR = "bottom-sensor"
    MOVEMENT = "movement"
    BACK = "back"


class Extension(Enum):
    DISABLED = "disabled"
    CUSTOM = "custom"
    CAMERA_2_AXIS = "camera-2-axis"
    ROBOT_ARM = "robot-arm"
    BUTTON_PRESSER = "button-presser"
    COLOR_SENSOR = "color-sensor"
    DRIVE_4_WHEELS = "4-wheel-drive"
    DRIVE_2_WHEELS = "2-wheel-drive"
    CLAW = "claw"


EXTENSION_DISPLAY_INFO = {
    Extension.DISABLED: ["Disabled", "No extensions connected"]
}


def extension_enum_entry(extension):
    # TODO: Add all Extensions to EXTENSION_DISPLAY_INFO
    # return {
    #   "value": extension.value,
    #   "title":EXTENSION_DISPLAY_INFO[extension][0],
    #   "description": EXTENSION_DISPLAY_INFO[extension][1]
    # }
    return {"value": extension.value}


def default_slot_config():
    return {
        Slot.MOVEMENT.value: {
            "title": "Movement Slot (sides)",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.DRIVE_4_WHEELS),
                extension_enum_entry(Extension.DRIVE_2_WHEELS),
                extension_enum_entry(Extension.DISABLED),
                extension_enum_entry(Extension.CUSTOM),
            ],
        },
        Slot.TOP_FRONT.value: {
            "title": "Top Front Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.CAMERA_2_AXIS),
                extension_enum_entry(Extension.DISABLED),
                extension_enum_entry(Extension.CUSTOM),
            ],
        },
        Slot.TOP_BACK.value: {
            "title": "Top Back Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.ROBOT_ARM),
                extension_enum_entry(Extension.BUTTON_PRESSER),
                extension_enum_entry(Extension.DISABLED),
                extension_enum_entry(Extension.CUSTOM),
            ],
        },
        Slot.BOTTOM_FRONT.value: {
            "title": "Bottom Front Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.CLAW),
                extension_enum_entry(Extension.BUTTON_PRESSER),
                extension_enum_entry(Extension.DISABLED),
                extension_enum_entry(Extension.CUSTOM),
            ],
        },
        Slot.BOTTOM_SENSOR.value: {
            "title": "Bottom Sensor Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.CLAW),
                extension_enum_entry(Extension.BUTTON_PRESSER),
                extension_enum_entry(Extension.DISABLED),
                extension_enum_entry(Extension.CUSTOM),
            ],
        },
    }


def generate_configs(templates, default_game_type):
    game_type_group = {"children": {}, "title": "Game Settings"}
    root_config = {"children": {"game-type-group": game_type_group}}
    game_type_enum_list = []
    for template_id, template in templates.items():
        enum_config = {"value": template_id}
        description = template.description()
        enum_config["description"] = "asd"
        if description:
            enum_config["description"] = description
        game_type_enum_list.append(enum_config)

    game_type_group["children"]["game-type"] = {
        "title": "Game Type",
        "valueType": ConfigType.STRING,
        "default": default_game_type,
        "enum": game_type_enum_list,
    }
    for template_id, template in templates.items():
        game_configs = template.game_configs()
        if game_configs:
            for config_id, config in game_configs.items():
                config["conditions"] = [
                    {"variable": ".game-type", "value": template_id}
                ]
                game_type_group["children"][
                    template_id + "-" + config_id
                ] = config

        template_slot_group = {
            "title": "Slot Configuration",
            "conditions": [
                {"variable": "game-type-group.game-type", "value": template_id}
            ],
        }

        template_slot_config = default_slot_config()
        # Filter to extensions given by template
        # NOTE: limits are only applied to slots present in the slot_limits
        limits = template.slot_limits()
        if limits:
            for slot, limits in limits.items():
                limit_to = limits["extensions"]
                template_slot_config[slot.value]["enum"] = list(
                    filter(
                        lambda slot_option: Extension(slot_option["value"])
                        in limit_to,
                        template_slot_config[slot.value]["enum"],
                    )
                )
                template_slot_config[slot.value]["default"] = limits[
                    "default"
                ].value

        template_slot_group["children"] = template_slot_config
        root_config["children"][
            "slot-config-" + template_id
        ] = template_slot_group

    return root_config


class ConfigParser:
    def __init__(self, game):
        self.game = game

    def configs(self):
        return self.game.configs["custom"]

    def current_template(self):
        return self.configs()["game-type-group"]["game-type"]

    def get_game_config(self, config_id):
        template_id = self.current_template()
        return self.configs()["game-type-group"][template_id + "-" + config_id]

    def get_slot_confgi(self, slot):
        template_id = self.current_template()
        return self.configs()["slot-config-" + template_id][slot.value]
