"""Wellington City Council (wellington.govt.nz).

Composes: :class:`~waste_collection_schedule.retrievers.LookupChainRetriever`
(a street-name-to-id POST lookup, then the ICS GET keyed on that id),
:class:`~waste_collection_schedule.parsers.ArgumentGuard` (the council answers
an unknown street id with an ordinary page rather than a feed) and
:class:`~waste_collection_schedule.preprocessors.SplitLabels` (one ICS summary
joins the day's rounds with "&"). ``classify()`` is used rather than a plain
transformer only to attach the provider's per-round picture, which
``ICSTransformer`` has no field for; the type resolution itself is still the
shared transformer's.
"""

import datetime
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import alternatives, location_id, street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import ArgumentGuard, IcsParser
from waste_collection_schedule.preprocessors import SplitLabels
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

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
        "rubbish collection": wt.GENERAL_WASTE,
        "glass crate": wt.GLASS,
        "wheelie bin or recycling bags": wt.RECYCLABLES,
    }
)


def _resolve_street(source: BaseSource, keys: tuple) -> str:
    """The council's street id: the one given, or the one the name resolves to.

    The lookup is a partial-name search, so it answers with every street whose
    name contains the term. Nothing matched is a misspelling; several matched is
    a term too short to identify one street, and both are the user's argument to
    correct rather than an empty schedule.
    """
    street_name = source.params.get("streetName")
    if not street_name:
        return str(source.params.get("streetId"))

    r = source.session.post(
        _STREET_LOOKUP_URL,
        json={"partialStreetName": street_name},
        headers=_HEADERS,
    )
    r.raise_for_status()
    matches = r.json().get("d") or []
    if len(matches) == 0:
        raise SourceArgumentNotFound("streetName", street_name)
    if len(matches) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "streetName",
            street_name,
            [m["Value"].split(",")[0] for m in matches],
        )
    return matches[0].get("Key")


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

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.GLASS, wt.RECYCLABLES]

    retrieve = LookupChainRetriever(
        steps=(_resolve_street,),
        url=_CALENDAR_URL,
        params=lambda street_id, **_: {
            "type": "recycling",
            "streetId": street_id,
            "forDate": datetime.date.today(),
        },
        headers=_HEADERS,
    )

    parse = ArgumentGuard(
        IcsParser(),
        argument="streetId",
        contains="BEGIN:VCALENDAR",
        hint="this is not a street id the council publishes a calendar for.",
    )

    # A day's rounds arrive as one summary, e.g. "Rubbish Collection & Glass
    # crate". Split rather than title-case (ICS split_at), because the parts are
    # looked up in _PICTURE_MAP exactly as the council spells them.
    preprocess = SplitLabels(r"&")

    def classify(self, record):
        date, label = record
        collection = _TYPE_TRANSFORM((date, label))
        if collection is None:
            return None
        picture = _PICTURE_MAP.get(label)
        if picture is not None and isinstance(collection, Collection):
            collection.set_picture(picture)
        return collection
