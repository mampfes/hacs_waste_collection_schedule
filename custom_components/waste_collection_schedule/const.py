"""Constants for the Waste Collection Schedule component."""

# Component domain, used to store component data in hass data.
DOMAIN = "waste_collection_schedule"

UPDATE_SENSORS_SIGNAL = "wcs_update_sensors_signal"

CONFIG_VERSION = 1

# Config var names
CONF_SOURCES = "sources"

CONF_COUNTRY_NAME = "country"

CONF_SOURCE_NAME = "name"
CONF_SOURCE_ARGS = "args"  # source arguments

CONF_SOURCE_CALENDAR_TITLE = "calendar_title"
CONF_SEPARATOR = "separator"
CONF_FETCH_TIME = "fetch_time"
CONF_RANDOM_FETCH_TIME_OFFSET = "random_fetch_time_offset"
CONF_DAY_SWITCH_TIME = "day_switch_time"

CONF_CUSTOMIZE = "customize"
CONF_TYPE = "type"
CONF_ALIAS = "alias"
CONF_SHOW = "show"
CONF_ICON = "icon"
CONF_PICTURE = "picture"
CONF_USE_DEDICATED_CALENDAR = "use_dedicated_calendar"
CONF_DEDICATED_CALENDAR_TITLE = "dedicated_calendar_title"

CONF_SEPARATOR_DEFAULT = ", "
CONF_FETCH_TIME_DEFAULT = "01:00"
CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT = 60
CONF_DAY_SWITCH_TIME_DEFAULT = "10:00"
