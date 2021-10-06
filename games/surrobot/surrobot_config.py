from enum import Enum

from surrortg.game_io import ConfigType


class Slot(Enum):
    TOP_FRONT = "topFront"
    TOP_BACK = "topBack"
    BOTTOM_FRONT = "bottomFront"
    BOTTOM_SENSOR = "bottomSensor"
    MOVEMENT = "movement"
    BACK = "back"


class Extension(Enum):
    DISABLED = "disabled"
    CUSTOM = "custom"
    CAMERA_2_AXIS = "camera2Axis"
    ROBOT_ARM = "robotArm"
    BUTTON_PRESSER = "buttonPresser"
    KNOB_TURNER = "knobTurner"
    SWITCH_FLICKER = "switchFlicker"
    LED_MATRIX = "ledMatrix"
    COLOR_SENSOR = "colorSensor"
    DRIVE_4_WHEELS = "drive4Wheels"
    DRIVE_2_WHEELS = "drive2Wheels"
    SEPARATE_MOTOR = "separateMotor"
    CLAW = "claw"


SLOT_SIZES = {
    Slot.MOVEMENT: 4,
    Slot.TOP_FRONT: 4,
    Slot.TOP_BACK: 3,
}

CUSTOM_EXTENSIONS = {
    Slot.MOVEMENT: [Extension.SEPARATE_MOTOR],
    Slot.TOP_FRONT: [
        Extension.BUTTON_PRESSER,
        Extension.KNOB_TURNER,
        Extension.SWITCH_FLICKER,
    ],
    Slot.TOP_BACK: [
        Extension.BUTTON_PRESSER,
        Extension.KNOB_TURNER,
        Extension.SWITCH_FLICKER,
    ],
}

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
            ],
        },
        Slot.TOP_FRONT.value: {
            "title": "Top Front Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.CAMERA_2_AXIS),
                extension_enum_entry(Extension.DISABLED),
            ],
        },
        Slot.TOP_BACK.value: {
            "title": "Top Back Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.ROBOT_ARM),
                extension_enum_entry(Extension.LED_MATRIX),
                extension_enum_entry(Extension.BUTTON_PRESSER),
                extension_enum_entry(Extension.KNOB_TURNER),
                extension_enum_entry(Extension.SWITCH_FLICKER),
                extension_enum_entry(Extension.DISABLED),
            ],
        },
        Slot.BOTTOM_FRONT.value: {
            "title": "Bottom Front Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.CLAW),
                extension_enum_entry(Extension.BUTTON_PRESSER),
                extension_enum_entry(Extension.KNOB_TURNER),
                extension_enum_entry(Extension.SWITCH_FLICKER),
                extension_enum_entry(Extension.DISABLED),
            ],
        },
        Slot.BOTTOM_SENSOR.value: {
            "title": "Bottom Sensor Slot",
            "valueType": ConfigType.STRING,
            "default": Extension.DISABLED.value,
            "enum": [
                extension_enum_entry(Extension.COLOR_SENSOR),
                extension_enum_entry(Extension.DISABLED),
            ],
        },
    }


def game_settings_group_id(template_id):
    return "gameSettingGroup" + template_id.capitalize()


def slot_group_id(template_id):
    return "slotGroup" + template_id.capitalize()


def generate_custom_options(template, base_config):
    limits = template.slot_limits()
    full_config = {}
    for slot_id, config in base_config.items():
        full_config[slot_id] = config
        slot = Slot(slot_id)
        if slot not in SLOT_SIZES or slot not in CUSTOM_EXTENSIONS:
            break
        custom_count = SLOT_SIZES[slot]
        custom_extensions = CUSTOM_EXTENSIONS[slot].copy()
        if limits and slot in limits:
            custom_limit = limits[slot]["extensions"]
            custom_extensions = list(
                filter(
                    lambda extension: extension in custom_limit,
                    custom_extensions,
                )
            )
        if custom_count > 1 and len(custom_extensions) > 0:
            custom_extensions.append(Extension.DISABLED)
            custom_enums = list(
                map(
                    lambda extension: extension_enum_entry(extension),
                    custom_extensions,
                )
            )
            config["enum"].append(extension_enum_entry(Extension.CUSTOM))
            for i in range(custom_count):
                custom_id = f"{slot_id}Custom{i}"
                full_config[custom_id] = {
                    "title": f"{config['title']} Custom {i+1}",
                    "valueType": ConfigType.STRING,
                    "default": Extension.DISABLED.value,
                    "enum": custom_enums,
                    "conditions": [
                        {
                            "variable": f".{slot_id}",
                            "value": Extension.CUSTOM.value,
                        }
                    ],
                }
    return full_config


def generate_configs(templates, default_game_type):
    game_type_group = {"children": {}, "title": "Game Type"}
    root_config = {"children": {"gameTypeGroup": game_type_group}}
    game_type_enum_list = []
    for template_id, template in templates.items():
        enum_config = {"value": template_id}
        description = template.description()
        enum_config["description"] = "asd"
        if description:
            enum_config["description"] = description
        game_type_enum_list.append(enum_config)

    game_type_group["children"]["gameType"] = {
        "title": "Game Type",
        "valueType": ConfigType.STRING,
        "default": default_game_type,
        "enum": game_type_enum_list,
    }
    for template_id, template in templates.items():

        game_configs = template.game_configs()
        if game_configs:
            game_settings_group = {
                "title": "Game Settings",
                "children": game_configs,
                "conditions": [
                    {
                        "variable": "gameTypeGroup.gameType",
                        "value": template_id,
                    }
                ],
            }
            root_config["children"][
                game_settings_group_id(template_id)
            ] = game_settings_group

        template_slot_group = {
            "title": "Slot Configuration",
            "conditions": [
                {"variable": "gameTypeGroup.gameType", "value": template_id}
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

        config_with_custom_option = generate_custom_options(
            template, template_slot_config
        )

        template_slot_group["children"] = config_with_custom_option
        root_config["children"][
            slot_group_id(template_id)
        ] = template_slot_group

    return root_config


class ConfigParser:
    def __init__(self, game):
        self.game = game

    def configs(self):
        return self.game.configs["custom"]

    def current_template(self):
        return self.configs()["gameTypeGroup"]["gameType"]

    def get_game_config(self, config_id):
        template_id = self.current_template()
        return self.configs()[game_settings_group_id(template_id)][config_id]

    def get_slot_config(self, slot):
        template_id = self.current_template()
        extension_id = self.configs()[slot_group_id(template_id)][slot.value]
        return Extension(extension_id)

    def get_slot_custom_config(self, slot):
        template_id = self.current_template()
        extension_ids = []
        for i in range(SLOT_SIZES[slot]):
            slot_group = self.configs()[slot_group_id(template_id)]
            config_name = f"{slot.value}Custom{i}"
            if config_name in slot_group:
                extension_ids.append(slot_group[config_name])
        return map(lambda extension_id: Extension(extension_id), extension_ids)
