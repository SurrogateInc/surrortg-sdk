from enum import Enum


class ConfigType(Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"


"""
EXAMPLE_CONF = {
    "children": {
        "myconf": {
            "title": "My conf displayname",
            "description": "Describes the conf in detail",
            "valueType": ConfigType.NUMBER,
            "default": 1,
            "enum": [
                { "value": 1, "description": "description when selected" },
                { "value": 2, "description": "another description" },
            ],
        },
        "condconf": {
            "title": "Conditional config",
            "valueType": ConfigType.BOOLEAN,
            "default": False,
            "conditions": [
                { "variable": "myconf", "value": 1 },
                { "variable": "mygroup.mysubconf", "value": 3 },
            ],
        },
        "mygroup": {
            "conditions": [
                { "variable": "myconf", "value": 1 },
            ],
            "children": {
                "mysubconf": {
                    "title": "My Sub Conf",
                    "valueType": ConfigType.INTEGER,
                    "default": 3,
                    "minimum": 2,
                    "maximum": 50,
                },
                "myothersubconf": {
                    "valueType": ConfigType.BOOLEAN,
                    "default": False,
                },
            },
        },
    }
}
"""

EMPTY_CONFIG = {"children": {}}


def check_conditions(config, parent, root):
    if "conditions" not in config:
        return
    for condition in config["conditions"]:
        assert condition.keys() <= {
            "variable",
            "value",
        }, "there were extra items in a condition"
        assert isinstance(condition["variable"], str)
        is_relative = condition["variable"][0] == "."
        real_root = parent if is_relative else root
        try:
            for part in filter(None, condition["variable"].split(".")):
                real_root = real_root["children"][part]
        except KeyError:
            var = condition["variable"]
            raise AssertionError(f"Condition {var} not found")
        value_type = real_root["valueType"]
        if type(value_type) is not str:
            value_type = value_type.value
        types = get_config_types(value_type)
        assert isinstance(condition["value"], types)


def check_title(id, config):
    assert "title" not in config or isinstance(
        config["title"], str
    ), f"[{id}] Display name must be a string"


def check_config_group(id, group, root):
    assert group.keys() <= {
        "title",
        "conditions",
        "children",
    }, "there were extra items in group"
    check_title(id, group)
    for id, config in group["children"].items():
        check_config_entry(id, config, group, root)


def check_config_variable(id, variable, root):
    assert variable.keys() <= {
        "valueType",
        "default",
        "minimum",
        "maximum",
        "enum",
        "title",
        "description",
        "conditions",
        "children",
    }, "there were extra items in config"
    check_title(id, variable)
    assert "description" not in variable or isinstance(
        variable["description"], str
    ), f"[{id}] Description must be a string"
    value_type = variable["valueType"]
    assert isinstance(value_type, ConfigType) or ConfigType(value_type), (
        f"[{id}] 'value_type' must be a valid ConfigType ",
        "(string | number | integer | bool)",
    )
    if type(value_type) is not str:
        value_type = value_type.value
        variable["valueType"] = value_type
    default = variable["default"]
    maximum = variable["maximum"] if "maximum" in variable else None
    minimum = variable["minimum"] if "minimum" in variable else None
    enum = variable["enum"] if "enum" in variable else None
    types_to_check = get_config_types(value_type)
    assert isinstance(
        default, types_to_check
    ), f"'default' must be a {value_type}"

    minmax_values = tuple(set(types_to_check).intersection(set([int, float])))
    for val in [minimum, maximum]:
        assert val is None or isinstance(val, minmax_values)
        f"[{id}] min/max val has to be float, int or None"

    if enum is not None:
        assert (
            isinstance(enum, list) and len(enum) > 0
        ), "Enum must be a non-empty list"
        for val in enum:
            assert isinstance(
                val["value"], types_to_check
            ), f"enum values must be of type {value_type}"
            assert "description" not in val or isinstance(
                val["description"], str
            ), "Enum description must be a string"
        assert default in map(
            lambda x: x["value"], enum
        ), "Default value must be one of enum values"

    if minimum is not None:
        assert default >= minimum, "'default' must be at least minimum"
    if maximum is not None:
        assert default <= maximum, "'default' must be at most maximum"

    if enum is not None:
        assert (
            minimum is None and maximum is None
        ), "enum and min/max are mutually exclusive"


def check_config_entry(id, config, parent, root):
    check_conditions(config, parent, root)
    if "children" in config:
        check_config_group(id, config, root)
    else:
        check_config_variable(id, config, root)


def get_config_types(value_type):
    types_to_check = ()
    if value_type == "string":
        types_to_check = (str,)
    elif value_type == "number":
        types_to_check = (int, float)
    elif value_type == "integer":
        types_to_check = (int,)
    elif value_type == "boolean":
        types_to_check = (bool,)
    return types_to_check


EMPTY_CONFIG = {"children": {}}
