import datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://www.schweinfurt.de/umweltverkehr/abfall--entsorgung/mllkalender/14894.Aktuelle-Abfuhrtermine-und-Muellkalender.html"

# Titles (or title fragments) that are announcements rather than an actual
# collection/drop-off event, e.g. "Wertstoffhof geschlossen" (recycling
# center closed) or "Aktion Kompostverkauf" (compost sale campaign). These
# are never useful as a "collection" entry, so they are always filtered
# out, regardless of the `showmobile` setting.
NON_COLLECTION_KEYWORDS = ["geschlossen", "Aktion Kompostverkauf"]


def _address_id(response, address, **_) -> str:
    """Pick the value of the street <option> that contains the address."""
    options = [
        (tag.text.strip(), tag.get("value"))
        for tag in BeautifulSoup(response.text, "html.parser").find_all("option")
        if tag.get("value")
    ]
    matches = [value for text, value in options if address in text]
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, [text for text, _ in options]
        )
    return matches[-1]


def _query(addr_id, **_) -> dict:
    today = datetime.date.today()
    return {
        "_func": "evList",
        "_mod": "events",
        "ev[start]": today.strftime("%Y-%m-%d"),
        "ev[end]": (today + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
        "ev[addr]": addr_id,
    }


def _keep(record, source) -> bool:
    title = record["title"]
    if any(k.lower() in title.lower() for k in NON_COLLECTION_KEYWORDS):
        return False
    # showmobile may arrive as a quoted YAML string ("False" is truthy).
    show_mobile = str(source.params.get("showmobile")).strip().lower() == "true"
    return show_mobile or "Wertstoffhof" not in title


def _location(record) -> str | None:
    """The stop of a mobile collection ("... - Goethestraße")."""
    _, sep, place = record["title"].partition(" - ")
    return place if sep else None


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Stadt Schweinfurt"
    DESCRIPTION = "Source for Schweinfurt, Germany"
    URL = "https://www.schweinfurt.de"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestcaseI": {"address": "Ahornstrasse"},
        "TestcaseII": {"address": "Ahornstrasse", "showmobile": "True"},
        "TestcaseIII": {"address": "Ahornstrasse", "showmobile": "False"},
        "TestcaseIV": {"address": "Ahornstrasse", "showmobile": False},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.PAPER,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
    ]

    PARAMS = (
        street_address(),
        boolean("showmobile", "Show mobile recycling center", default=False),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name as listed in the street dropdown at "
            "https://www.schweinfurt.de (e.g. 'Ahornstrasse'). Enable "
            "'showmobile' to also include the mobile recycling center "
            "(Mobiler Wertstoffhof) dates."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(API_URL, pick=_address_id),),
        url=API_URL,
        params=_query,
        headers={"referer": API_URL},
        raise_for_status=True,
    )
    parse = parsers.JsonParser("contents")
    preprocess = preprocessors.Compose(
        preprocessors.FlattenGroups(),
        preprocessors.RowFilter(_keep),
    )
    transform = JsonTransformer(
        date_key="start",
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d %H:%M:%S"),
        clean=lambda title: title.partition(" - ")[0],
        location_key=_location,
        type_value_map={
            "Papier, Restmüll, Gelber Sack": [
                wt.PAPER,
                wt.GENERAL_WASTE,
                wt.RECYCLABLES,
            ],
            "Mobiler Wertstoffhof und Problemabfallsammlung": [
                wt.HAZARDOUS,
                wt.RECYCLABLES,
            ],
        },
    )
