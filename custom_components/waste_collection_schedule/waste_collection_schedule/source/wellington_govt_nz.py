"""Wellington City Council (wellington.govt.nz).

Demonstrates: a street-name-to-id POST lookup (returning suggestions on a
mismatch/ambiguity) followed by an ICS GET keyed on that id, then splitting a
single "&"-joined ICS summary into several same-day entries, each carrying its
own icon and picture. No configured retriever expresses a POST-based lookup
with ambiguous-match handling, hence a source-defined retrieve(); classify()
is used (rather than a plain transformer) only to reuse a shared type
resolver while attaching the provider's per-type picture URL, which
ICSTransformer has no field for.
"""

import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import alternatives, location_id, street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, GLASS, RECYCLABLES

_BASE_URL = "https://wellington.govt.nz"
_STREET_LOOKUP_URL = (
    f"{_BASE_URL}/layouts/wcc/GeneralLayout.aspx/GetRubbishCollectionStreets"
)
_CALENDAR_URL = f"{_BASE_URL}/~/ical/"

_HEADERS = {"User-Agent": "Mozilla/5.0 Gecko/20100101 Firefox/136.0"}

_PICTURE_MAP = {
    "Rubbish Collection": f"{_BASE_URL}/assets/images/rubbish-recycling/rubbish-bag.png",
    "Glass crate": f"{_BASE_URL}/assets/images/rubbish-recycling/glass-crate.png",
    "Wheelie bin or recycling bags": f"{_BASE_URL}/assets/images/rubbish-recycling/wheelie-bin.png",
}

# The type resolver only, reused inside classify() so the picture attachment
# below doesn't have to reimplement label -> WasteType resolution.
_TYPE_TRANSFORM = ICSTransformer(
    type_value_map={
        "rubbish collection": GENERAL_WASTE,
        "glass crate": GLASS,
        "wheelie bin or recycling bags": RECYCLABLES,
    }
)


@final
class Source(BaseSource):
    TITLE = "Wellington City Council"
    DESCRIPTION = "Source for Wellington City Council."
    URL = _BASE_URL
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Chelsea St": {"streetName": "Cheltenham Terrace"},  # Friday
        "Campbell St (ID Only)": {"streetId": "6515"},  # Wednesday
    }

    PARAMS = (
        alternatives([location_id(field="streetId")], [street(field="streetName")]),
    )

    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, GLASS, RECYCLABLES]

    def retrieve(self, source):
        session = source.session
        street_id = source.params.get("streetId")
        street_name = source.params.get("streetName")

        if street_name:
            r = session.post(
                _STREET_LOOKUP_URL,
                json={"partialStreetName": street_name},
                headers=_HEADERS,
            )
            r.raise_for_status()
            data = r.json()
            matches = data.get("d") or []
            if len(matches) == 0:
                raise SourceArgumentNotFound("streetName", street_name)
            if len(matches) > 1:
                raise SourceArgAmbiguousWithSuggestions(
                    "streetName",
                    street_name,
                    [m["Value"].split(",")[0] for m in matches],
                )
            street_id = matches[0].get("Key")

        r = session.get(
            _CALENDAR_URL,
            params={
                "type": "recycling",
                "streetId": street_id,
                "forDate": datetime.date.today(),
            },
            headers=_HEADERS,
        )
        if not r.text.startswith("BEGIN:VCALENDAR"):
            raise SourceArgumentException(
                "streetId", f"{street_id} is not a valid streetID"
            )
        return r

    parse = IcsParser()

    def preprocess(self, records, source=None):
        for date, label in records:
            for part in label.split("&"):
                part = part.strip()
                if part:
                    yield (date, part)

    def classify(self, record):
        date, label = record
        collection = _TYPE_TRANSFORM((date, label))
        if collection is None:
            return None
        picture = _PICTURE_MAP.get(label)
        if picture is not None and isinstance(collection, Collection):
            collection.set_picture(picture)
        return collection

    def __init__(self, streetId: "str | None" = None, streetName: "str | None" = None):
        super().__init__(streetId=streetId, streetName=streetName)
