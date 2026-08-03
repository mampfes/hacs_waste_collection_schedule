"""Mid Devon District Council - Collection Day Lookup.

Retrieves collection schedules from the council's Collection Day Lookup API.
Gets a session via the standard AchieveForms handshake, submits the UPRN via
runLookup (id=642315aacb919), and reads the response, which comes back in one
of two shapes: a "display" (date) + "CollectionItems" (one or more bin names,
joined by "and") row, or a bare "display" + "CollectionDay" (a weekday name)
row with no item breakdown. The two are a fallback chain over the same row, so
AchieveFormsRowFieldsPreprocessor reads whichever the property has.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowFieldsPreprocessor,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

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


@final
class Source(BaseSource):
    TITLE = "Mid Devon District Council"
    DESCRIPTION = "Source for waste collection services for Mid Devon District Council"
    URL = "https://www.middevon.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
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
    # CollectionItems, when present, names every bin collected that day; a row
    # without it falls back to the collection day name. The provider's feed can
    # repeat a row, so identical (date, item) pairs are emitted once.
    preprocess = AchieveFormsRowFieldsPreprocessor(
        date_field="display",
        label_fields=("CollectionItems", "CollectionDay"),
        first_label_only=True,
        split_labels=_ITEM_SPLIT_RE,
        parse_date=date_parsers.for_format("%d-%b-%y"),
        dedupe=True,
    )
    transform = RowTransformer(
        type_value_map={
            "blue food caddy": wt.FOOD_WASTE,
            "black & green recycling boxes": wt.RECYCLABLES,
            "black and green recycling boxes": wt.RECYCLABLES,
            "green recycling box": wt.RECYCLABLES,
            "black recycling box": wt.RECYCLABLES,
            "garden waste": wt.GARDEN_WASTE,
            "domestic refuse": wt.GENERAL_WASTE,
            "black bin": wt.GENERAL_WASTE,
            "rubbish": wt.GENERAL_WASTE,
        },
    )
