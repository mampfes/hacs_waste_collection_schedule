import urllib

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfalltermine Fürth"
DESCRIPTION = "Source for Stadt Fürth"
URL = "https://abfallwirtschaft.fuerth.eu/"
TEST_CASES = {
    "Flößaustraße": {"city": "Fürth", "area": "Flößaustraße"},
    "Ullsteinstraße": {"city": "Fürth", "area": "Ullsteinstraße"},
    "Fürther Freiheit": {
        "city": "Fürth",
        "area": "Fürther Freiheit 6",
    },
}

# HERE COMES THE MAGIC :D