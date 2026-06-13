from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    OTHER,
    PAPER,
    RECYCLABLES,
    WasteType,
)

# Demonstrates: parsers.ics_events + the classify() escape hatch.
# Notable: per-route filtering (yellow_route / paper_route) needs the ICS
# LOCATION / DESCRIPTION fields, which the (date, summary) tuples from
# parsers.ics discard. parsers.ics_events exposes the full IcsEvent, and
# classify() does the route filtering plus route-suffix-aware type mapping
# ("Gelbe Tonne 2", "Papier Ost", ...) that a standard transformer can't.

# Bin type (lower-cased, "Entsorgung " prefix and any route suffix removed) -> type.
_TYPE_MAP: dict[str, WasteType] = {
    "gelbe tonne": RECYCLABLES,
    "bioabfall": ORGANIC,
    "restabfall": GENERAL_WASTE,
    "papier": PAPER,
    "sperrmüll": BULKY_WASTE,
    "weiße ware": BULKY_WASTE,
    "kühlgeräte": BULKY_WASTE,
}


class Source(BaseSource):
    TITLE = "MZV Rotenburg"
    DESCRIPTION = "Source for MZV Rotenburg."
    URL = "https://www.mzv-rotenburg-bebra.de"
    COUNTRY = "de"
    API_URL = "https://www.mzv-rotenburg-bebra.de/entsorgung.php"

    TEST_CASES = {
        "Rotenburg an der Fulda": {"city": "rote"},
        "Bebra": {"city": "bebra"},
        "Rotenburg an der Fulda 2 Ost": {
            "city": "rote",
            "yellow_route": "2",
            "paper_route": "Ost",
        },
    }

    PARAMS = [
        text_field("city", "City"),
        text_field("yellow_route", "Gelbe Tonne Route"),
        text_field("paper_route", "Papier Route"),
    ]

    HOWTO = {
        "de": (
            "Der Ort muss genau wie im `ort`-URL-Parameter der Links auf "
            "https://www.mzv-rotenburg-bebra.de//webapp.html geschrieben werden "
            "(z.B. `rote`, `bebra`). yellow_route / paper_route filtern nach "
            "Sammelroute, falls der Ort mehrere Routen hat."
        ),
    }

    # classify() produces these — declared explicitly (no transformer to derive from).
    WASTE_TYPES = [RECYCLABLES, ORGANIC, GENERAL_WASTE, PAPER, BULKY_WASTE, OTHER]

    parse = parsers.ics_events

    def __init__(
        self,
        city: str,
        yellow_route: str | None = None,
        paper_route: str | None = None,
    ):
        self._yellow_route = yellow_route
        self._paper_route = paper_route
        self._params = {"ort": city}
        self._headers = {"User-Agent": "Mozilla/5.0"}

    def classify(self, record) -> Collection | None:
        summary = (record.title or "").strip()
        if not summary:
            return None

        # The route label may appear in the summary, location or description.
        route_context = " ".join(
            part for part in (record.title, record.location, record.description) if part
        ).lower()

        bin_type = summary.removeprefix("Entsorgung ").strip().lower()

        if bin_type.startswith("gelbe tonne"):
            if self._yellow_route and self._yellow_route.lower() not in route_context:
                return None
            bin_type = "gelbe tonne"
        elif bin_type.startswith("papier"):
            if self._paper_route and self._paper_route.lower() not in route_context:
                return None
            bin_type = "papier"

        return Collection(date=record.date, waste_type=_TYPE_MAP.get(bin_type, OTHER))
