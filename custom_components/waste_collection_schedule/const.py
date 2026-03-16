"""Constants for the Waste Collection Schedule component."""

from typing import Final

# Component domain, used to store component data in hass data.
DOMAIN: Final = "waste_collection_schedule"

UPDATE_SENSORS_SIGNAL: Final = "wcs_update_sensors_signal"

CONFIG_VERSION: Final = 2
CONFIG_MINOR_VERSION: Final = 13

# Config var names
CONF_SOURCES: Final = "sources"

CONF_COUNTRY_NAME: Final = "country"

CONF_SOURCE_NAME: Final = "name"
CONF_SOURCE_ARGS: Final = "args"  # source arguments

CONF_SOURCE_CALENDAR_TITLE: Final = "calendar_title"
CONF_SEPARATOR: Final = "separator"
CONF_FETCH_TIME: Final = "fetch_time"
CONF_RANDOM_FETCH_TIME_OFFSET: Final = "random_fetch_time_offset"
CONF_DAY_SWITCH_TIME: Final = "day_switch_time"

CONF_CUSTOMIZE: Final = "customize"
CONF_TYPE: Final = "type"
CONF_ALIAS: Final = "alias"
CONF_SHOW: Final = "show"
CONF_ICON: Final = "icon"
CONF_PICTURE: Final = "picture"
CONF_USE_DEDICATED_CALENDAR: Final = "use_dedicated_calendar"
CONF_DEDICATED_CALENDAR_TITLE: Final = "dedicated_calendar_title"
CONF_DAY_OFFSET = "day_offset"
CONF_DAY_OFFSET_DEFAULT = 0

CONF_SEPARATOR_DEFAULT: Final = ", "
CONF_FETCH_TIME_DEFAULT: Final = "01:00"
CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT: Final = 60
CONF_DAY_SWITCH_TIME_DEFAULT: Final = "10:00"

# Sensor config var names

CONF_SOURCE_INDEX: Final = "source_index"
CONF_DETAILS_FORMAT: Final = "details_format"
CONF_COUNT: Final = "count"
CONF_LEADTIME: Final = "leadtime"
CONF_DATE_TEMPLATE: Final = "date_template"
CONF_COLLECTION_TYPES: Final = "types"
CONF_ADD_DAYS_TO: Final = "add_days_to"
CONF_EVENT_INDEX: Final = "event_index"


CONF_SENSORS: Final = "sensors"
