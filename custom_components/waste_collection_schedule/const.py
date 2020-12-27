"""Constants for the Waste Collection Schedule component."""

# Component domain, used to store component data in hass data.
DOMAIN = "waste_collection_schedule"

UPDATE_SENSORS_SIGNAL = "wcs_update_sensors_signal"

# configuration variables
CONF_SOURCES = "sources"
CONF_SOURCE_NAME = "name"
CONF_SOURCE_ARGS = "args"  # scraper-source arguments
CONF_SEPARATOR = "separator"
CONF_FETCH_TIME = "fetch_time"
CONF_RANDOM_FETCH_TIME_OFFSET = "random_fetch_time_offset"
CONF_DAY_SWITCH_TIME = "day_switch_time"

# service specific variables
CONF_SERVICE = "service"
CONF_CITY_ID = "city_id"

# default values for some configuration variables
DEFAULT_SEPARATOR = ", "
DEFAULT_FETCH_TIME = "01:00"
DEFAULT_RANDOM_FETCH_TIME_OFFSET = 60
DEFAULT_DAY_SWITCH_TIME = "10:00"
