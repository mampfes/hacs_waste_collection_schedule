"""Mid Devon District Council - Collection Day Lookup.

Retrieves collection schedules from the council's Collection Day Lookup API.
Gets a session via the standard AchieveForms handshake, submits the UPRN via
runLookup (id=642315aacb919), and classifies the response, which comes back
in one of two shapes: a "display" (date) + "CollectionItems" (one or more
bin names, joined by "and") row, or a bare "display" + "CollectionDay" (a
weekday name) row with no item breakdown. classify() is used rather than a
standard transformer because a single row can expand into several
Collections (one per item) and because the two shapes need different label
sources.
"""

import re
from collections.abc import Iterable
from datetime import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import Collection
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
    WasteType,
    preserved,
    resolve,
)

# Live-verified (2026-07): the standard AchieveForms handshake
# (init_session -> authapi/isauthenticated, using the landing page's resolved
# URL) authenticates my.middevon.gov.uk without the legacy source's
# regex-scrape of the form page's embedded `auth-session` value. No
# service-layer change needed.
HOSTNAME = "my.middevon.gov.uk"
FORM_PAGE_URL = (
    "https://my.middevon.gov.uk/en/AchieveForms/"
    "?form_uri=sandbox-publish://AF-Process-2289dd06-9a12-4202-ba09-857fe756f6bd/"
    "AF-Stage-eb382015-001c-415d-beda-84f796dbb167/definition.json"
    "&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
)
LOOKUP_ID = "642315aacb919"

# Live-observed CollectionItems value: "Blue Food Caddy and Black & Green
# Recycling Boxes" -- items are joined by the WORD "and"; the "&" is part of
# a single item's own name ("Black & Green Recycling Boxes"). The legacy
# source's split regex (`\s+(?:and|&)\s+`) also split on that internal "&",
# producing a spurious extra "Black" fragment; this only splits on "and".
_ITEM_SPLIT_RE = re.compile(r"\s+and\s+", re.IGNORECASE)

_TYPE_VALUE_MAP: dict[str, "WasteType | list[WasteType]"] = {
    "blue food caddy": FOOD_WASTE,
    "black & green recycling boxes": RECYCLABLES,
    "black and green recycling boxes": RECYCLABLES,
    "green recycling box": RECYCLABLES,
    "black recycling box": RECYCLABLES,
    "garden waste": GARDEN_WASTE,
    "domestic refuse": GENERAL_WASTE,
    "black bin": GENERAL_WASTE,
    "rubbish": GENERAL_WASTE,
}


def _resolve_label(label: str) -> "WasteType | list[WasteType]":
    """Map a raw item label to a WasteType, never losing information.

    Same non-lossy order a standard transformer would use: the explicit map,
    then the shared multilingual vocabulary, then the label preserved
    verbatim -- classify() has no transformer to do this automatically.
    """
    key = label.strip().lower()
    if key in _TYPE_VALUE_MAP:
        return _TYPE_VALUE_MAP[key]
    waste_type = resolve(label)
    if waste_type is not None:
        return waste_type
    return preserved(label)


@final
class Source(BaseSource):
    TITLE = "Mid Devon District Council"
    DESCRIPTION = "Source for waste collection services for Mid Devon District Council"
    URL = "https://www.middevon.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list[WasteType]] = [
        FOOD_WASTE,
        RECYCLABLES,
        GENERAL_WASTE,
        GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Bradninch": {"uprn": 100040359199},
        "Bradninch - string": {"uprn": "100040359199"},
        "Cullompton": {"uprn": 100040354099},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=FORM_PAGE_URL,
        steps=[
            LookupStep(
                LOOKUP_ID,
                form_values=lambda ctx, source: {
                    "UPRN": {"name": "UPRN", "value": source.params["uprn"]},
                    "listAddress": {
                        "name": "listAddress",
                        "value": source.params["uprn"],
                    },
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[dict]":
        # A shared per-fetch dedupe set: the provider's feed can repeat a row.
        self._seen: set[tuple] = set()
        if isinstance(rows, dict):
            yield from (row for row in rows.values() if isinstance(row, dict))
        elif isinstance(rows, list):
            yield from (row for row in rows if isinstance(row, dict))

    def classify(self, record: dict) -> "Collection | list[Collection] | None":
        display = record.get("display")
        if not display:
            return None
        try:
            collection_date = datetime.strptime(display, "%d-%b-%y").date()
        except ValueError:
            return None

        items_str = record.get("CollectionItems")
        if items_str:
            labels = [
                part.strip() for part in _ITEM_SPLIT_RE.split(items_str) if part.strip()
            ]
        else:
            # No item breakdown for this row; fall back to the collection
            # day name, matching the legacy source's fallback shape.
            collection_day = str(record.get("CollectionDay") or "").strip()
            labels = [collection_day] if collection_day else []

        collections: list[Collection] = []
        for label in labels:
            key = (collection_date, label.lower())
            if key in self._seen:
                continue
            self._seen.add(key)
            resolved = _resolve_label(label)
            if isinstance(resolved, list):
                collections.extend(
                    Collection(date=collection_date, waste_type=wt) for wt in resolved
                )
            else:
                collections.append(
                    Collection(date=collection_date, waste_type=resolved)
                )

        if not collections:
            return None
        return collections if len(collections) > 1 else collections[0]
