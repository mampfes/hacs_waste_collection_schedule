import importlib
import logging

URL = None
TITLE = "Multiple Sources"
DESCRIPTION = "Source wrapper for multiple waste collection schedules."

TEST_CASES = {
    "two static": {
        "static": [
            {"type": "Dates only", "dates": ["2022-01-01", "2022-01-01"]},
            {
                "type": "First day of month",
                "frequency": "MONTHLY",
                "interval": 1,
                "start": "2022-01-01",
                "until": "2022-12-31",
            },
        ],
    },
    "multiple ics": {
        "ics": [
            {
                "url": "https://servicebetrieb.koblenz.de/abfallwirtschaft/entsorgungstermine-digital/entsorgungstermine-2023-digital/altstadt-2023.ics?cid=2ui7"
            },
            {
                "url": "https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics",
                "split_at": "\\, (?:and )?|(?: and )",
            },
        ]
    },
    "static and ics": {
        "static": {"type": "Dates only", "dates": ["2022-01-01", "2022-01-01"]},
        "ics": {
            "url": "https://sperrmuell.erlensee.de/?type=reminder",
            "method": "POST",
            "params": {
                "street": 8,
                "eventType[]": [27, 23, 19, 20, 21, 24, 22, 25, 26],
                "timeframe": 23,
                "download": "ical",
            },
        },
    },
    "multiple different sources": {
        "lund_se": {"street_address": "Lokföraregatan 7, LUND (19120)"},
        "meinawb_de": {
            "city": "Oberzissen",
            "street": "Lindenstrasse",
            "house_number": "1",
        },
        "jumomind_de": {
            "service_id": "mymuell",
            "city": "Bad Wünnenberg-Bleiwäsche",
        },
    },
    "multiple different with two static": {
        "lund_se": {"street_address": "Lokföraregatan 7, LUND (19120)"},
        "nawma_sa_gov_au": {
            "street_number": "128",
            "street_name": "Bridge Road",
            "suburb": "Pooraka",
        },
        "static": [
            {"type": "Dates only", "dates": ["2024-01-01", "2024-01-24"]},
            {
                "type": "First day of month",
                "frequency": "MONTHLY",
                "interval": 1,
                "start": "2022-01-01",
                "until": "2022-12-31",
            },
        ],
    },
}

LOGGER = logging.getLogger(__name__)


def get_source(source: str, args: dict | list[dict]) -> list:
    if isinstance(args, list):
        return [
            getattr(
                importlib.import_module(f"waste_collection_schedule.source.{source}"),
                "Source",
            )(**arg)
            for arg in args
        ]
    return [
        getattr(
            importlib.import_module(f"waste_collection_schedule.source.{source}"),
            "Source",
        )(**args)
    ]


def check_source_type(data):
    """Check if the type of 'data' matches either 'dict[str, dict]' or 'dict[str, list[dict]]'."""
    if isinstance(data, dict):
        # Check if all keys are strings
        if all(isinstance(key, str) for key in data.keys()):
            # Check if all values are either dictionaries or lists of dictionaries
            if all(
                isinstance(value, dict)
                or (
                    isinstance(value, list)
                    and all(isinstance(value2, dict) for value2 in value)
                )
                for value in data.values()
            ):
                return True
    return False


class Source:
    def __init__(self, **sources: dict[str, dict] | dict[str, list[dict]]):
        # test for correct source format

        if not check_source_type(sources):
            raise ValueError(
                f"Invalid source format provided should be a list of dictionaries or a list of list of dictionaries but is {type(sources)}, please take a look at the examples"
            )
        self._sources: list = []
        for source, args in sources.items():
            self._sources += get_source(source, args)

    def fetch(self):
        dates = []
        fails = 0
        for source in self._sources:
            try:
                dates.extend(source.fetch())
            except Exception as e:
                fails += 1
                LOGGER.error(f"Error fetching dates from source {source}: {e}")

        if fails == len(self._sources):
            raise RuntimeError("Failed to fetch dates from all sources")
        return dates
