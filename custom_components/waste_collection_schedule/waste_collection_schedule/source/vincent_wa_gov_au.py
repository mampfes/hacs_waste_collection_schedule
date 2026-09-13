import datetime
import re
from typing import ClassVar, final

import requests
from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.Pozi import (
    PoziError,
    PoziWfsParser,
    PoziWfsRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Demonstrates: a Pozi WFS spatial-query lookup by address (geocoded via the
# shared ArcGIS World GeocodeServer). Each collection field is an HTML-ish
# string like "15 Apr 2026 - Weekly (Wednesday)"; _describe() strips the
# markup and turns the date/frequency/day into Schedule descriptors. Labels
# ("General Waste", "Recycling", "FOGO") all resolve against the shared
# multilingual vocabulary, so no type_value_map is needed.
#
# The council's own mapping host still advertises the Waste_Collection layer
# but serves no features for it any more (#7281). Its Pozi viewer reads the
# same QGIS project through the tenant's dataset proxy instead, so the WFS
# endpoint is looked up live via DATASETS_API_URL rather than hard-coded: the
# proxy id changes whenever the council republishes the project. The proxy
# URL already points at a project, so PoziWfsRetriever is used with no
# map_path (unlike a plain QGIS WFS server, which needs one).

DATASETS_API_URL = "https://vincent.pozi.com/api/v1/public/maps/waste/datasets"
QGIS_PROJECT_DATASET_TYPE = 1
WFS_TYPENAME = "Waste_Collection"


def _waste_dataset_url(**_) -> str:
    """Look up the WFS endpoint of the council's current waste QGIS project."""
    r = requests.get(DATASETS_API_URL, timeout=30)
    r.raise_for_status()

    for group in r.json().get("mapdatasets", []):
        for dataset in group.get("datasets", []):
            if dataset.get("type") == QGIS_PROJECT_DATASET_TYPE and dataset.get("url"):
                return dataset["url"]

    raise PoziError(f"No QGIS project dataset advertised at {DATASETS_API_URL}")


# Matches: "15 Apr 2026 - Weekly (Wednesday)" or "15 Apr 2026 - Fortnightly (Thursday Week 2)"
# or "15 Apr 2026 - 2 x weekly (Wednesday/friday)"
_DATE_PATTERN = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})\s*-\s*(.+?)\s*\((.+?)\)")

# WFS field -> waste-type label.
_COLLECTION_FIELDS = (
    ("General Waste Collection Day", "General Waste"),
    ("FOGO Collection Day", "FOGO"),
    ("Recycling Collection Day", "Recycling"),
)

_WEEKLY_COUNT = 26
_FORTNIGHTLY_COUNT = 13


def _describe(zone, source):
    for field, label in _COLLECTION_FIELDS:
        raw = zone.get(field)
        if not raw:
            continue

        # Strip HTML tags, then the label prefix (e.g. "General Waste Collection Day:").
        text = re.sub(r"<[^>]+>", "", raw).strip()
        if ":" in text:
            text = text.split(":", 1)[1].strip()

        match = _DATE_PATTERN.search(text)
        if not match:
            continue
        date_str, frequency, day_info = match.groups()
        frequency = frequency.strip().lower()

        try:
            next_date = datetime.datetime.strptime(date_str, "%d %b %Y").date()
        except ValueError:
            continue

        if "2 x weekly" in frequency or "2x weekly" in frequency:
            # Twice-weekly collection: one weekly Schedule per day.
            for day_name in (d.strip().lower() for d in day_info.split("/")):
                weekday = recurrence.weekday(day_name)
                if weekday is None:
                    continue
                yield Schedule(
                    label,
                    recurrence.next_weekday(weekday),
                    recurrence.WEEKLY,
                    _WEEKLY_COUNT,
                )
        elif "fortnightly" in frequency:
            yield Schedule(label, next_date, recurrence.FORTNIGHTLY, _FORTNIGHTLY_COUNT)
        elif "weekly" in frequency:
            yield Schedule(label, next_date, recurrence.WEEKLY, _WEEKLY_COUNT)


@final
class Source(BaseSource):
    TITLE = "City of Vincent"
    DESCRIPTION = "Source for City of Vincent (WA) waste collection."
    URL = "https://www.vincent.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "North Perth": {"address": "8 Kadina St, North Perth WA 6006"},
        "Leederville": {"address": "18 Stamford St, Leederville WA"},
        "Mount Lawley": {"address": "28 Ruby St, North Perth WA"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address within the City of Vincent "
            "(e.g. '8 Kadina St, North Perth WA 6006')."
        ),
    }

    PARAMS = (street_address(),)

    retrieve = PoziWfsRetriever(_waste_dataset_url, WFS_TYPENAME, address="address")
    parse = PoziWfsParser()
    preprocess = RecurrenceExpander(_describe)
    transform = RowTransformer()
