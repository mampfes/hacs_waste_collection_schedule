"""Shared optional YAML fields for both supported sensor configuration paths."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .sensor_model import DATE_FORMATS, KINDS, LANGUAGES, STATE_FORMATS
from .waste_collection_schedule.colors import validate_color


def yaml_sensor_fields():
    return {
        vol.Optional("unique_id"): cv.string,
        vol.Optional("kind"): vol.In(KINDS),
        vol.Optional("exclude_types"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("unique_types", default=False): cv.boolean,
        vol.Optional("state_format"): vol.In(STATE_FORMATS),
        vol.Optional("language"): vol.In(LANGUAGES),
        vol.Optional("date_format"): vol.In(DATE_FORMATS),
        vol.Optional("color"): validate_color,
    }
