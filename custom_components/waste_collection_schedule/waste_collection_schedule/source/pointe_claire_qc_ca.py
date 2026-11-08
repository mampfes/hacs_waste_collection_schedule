import datetime
import re
import unicodedata
from typing import Literal

import icalendar
import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Pointe-Claire (QC)"
DESCRIPTION = "Source for Pointe-Claire, Québec waste collection schedules."
URL = "https://www.pointe-claire.ca"
TEST_CASES = {
    "Sector A": {"sector": "A"},
    "Sector B": {"sector": "B"},
}

ICON_MAP = {
    "Organic Waste": Icons.ORGANIC,
    "Recyclables": Icons.RECYCLING,
    "Household Waste": Icons.GENERAL_WASTE,
    "Bulky Items": Icons.BULKY,
    "Leaf Collection": Icons.GARDEN,
    "Christmas Tree Collection": Icons.CHRISTMAS_TREE,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your collection sector (A or B) with the City of Pointe-Claire address search tool at https://www.pointe-claire.ca/en/community-life/citizen-services/search-by-address",
    "fr": "Trouvez votre secteur de collecte (A ou B) avec l'outil de recherche par adresse de la Ville de Pointe-Claire à https://www.pointe-claire.ca/vie-communautaire/services-aux-citoyens/recherche-par-adresse",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "sector": "Collection sector (A or B)",
    },
    "fr": {
        "sector": "Secteur de collecte (A ou B)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "sector": "Sector",
    },
    "fr": {
        "sector": "Secteur",
    },
}

# Public iCal feed published by the city through its "Espace citoyen" portal.  # codespell:ignore espace
# The `collects` parameter selects the collection zone.
API_URL = "https://espace.pointe-claire.ca/avis/collectes/v2/calendrier.ics"  # codespell:ignore espace

SECTOR_ZONE_MAP: dict[str, int] = {
    "A": 2,
    "B": 3,
}

SECTOR_LITERAL = Literal["A", "B"]

# The city feed uses French event titles. They are mapped to the English type
# names this source has always exposed, so existing customisations keep working.
#
# 1. Event UIDs look like "2026-09-15-dechets@pointe-claire"; the code before
#    "@" is an internal identifier and the most stable way to classify events.
UID_TYPE_MAP = {
    "dechets": "Household Waste",
    "compost": "Organic Waste",
    "recyclage": "Recyclables",
    "encombrants": "Bulky Items",
    "verts": "Leaf Collection",
    "noel": "Christmas Tree Collection",
}
UID_CODE_RE = re.compile(r"-([a-z_]+)@", re.IGNORECASE)

# 2. Fallback: keywords in the (accent-stripped, lowercased) event title.
#    Order matters: "déchets verts" (green waste) must match before "dechet".
KEYWORD_TYPE_MAP = [
    (("noel", "sapin"), "Christmas Tree Collection"),
    (("feuille", "vert"), "Leaf Collection"),
    (("organique", "compost", "alimentaire"), "Organic Waste"),
    (("recycl",), "Recyclables"),
    (("encombr",), "Bulky Items"),
    (("dechet", "ordure"), "Household Waste"),
]


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return decomposed.encode("ascii", "ignore").decode("ascii").casefold()


def _collection_type(uid: str, title: str) -> str:
    match = UID_CODE_RE.search(uid)
    if match and match.group(1).lower() in UID_TYPE_MAP:
        return UID_TYPE_MAP[match.group(1).lower()]

    normalized = _normalize(title)
    for keywords, collection_type in KEYWORD_TYPE_MAP:
        if any(keyword in normalized for keyword in keywords):
            return collection_type

    # 3. Unknown event: keep the city's own title rather than dropping it.
    return title


class Source:
    def __init__(self, sector: SECTOR_LITERAL):
        self._sector = str(sector).upper().strip()

    def fetch(self) -> list[Collection]:
        zone = SECTOR_ZONE_MAP.get(self._sector)
        if zone is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "sector", self._sector, list(SECTOR_ZONE_MAP.keys())
            )

        r = requests.get(API_URL, params={"collects": zone}, timeout=30)
        r.raise_for_status()
        if "BEGIN:VCALENDAR" not in r.text:
            raise Exception(
                "Unexpected response from the Pointe-Claire calendar feed "
                "(not an iCalendar file)"
            )

        calendar = icalendar.Calendar.from_ical(r.text)
        entries = []
        for event in calendar.walk("VEVENT"):
            if "DTSTART" not in event:
                continue
            date = event.decoded("DTSTART")
            if isinstance(date, datetime.datetime):
                date = date.date()
            title = str(event.get("SUMMARY", "")).strip()
            collection_type = _collection_type(str(event.get("UID", "")), title)
            if not collection_type:
                continue
            entries.append(
                Collection(date, collection_type, ICON_MAP.get(collection_type))
            )

        # The feed also lists past collections, so an empty calendar means the
        # city changed its zone numbering or the feed is broken; fail visibly.
        if not entries:
            raise Exception(
                f"The Pointe-Claire calendar feed returned no collections for "
                f"sector {self._sector} (zone {zone})"
            )
        return entries
