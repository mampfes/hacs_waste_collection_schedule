import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import Response
from waste_collection_schedule.service.ArcGis import ArcGisFeatureParser, feature_query
from waste_collection_schedule.transformers import ICSTransformer

# Attribute query in two steps (address LIKE -> OBJECTID -> full record), then a
# mix of recurring schedules: weekly rubbish, fortnightly green/recycling from
# epoch-ms base dates, and a single street-sweeping date on a 6-week cycle.
# The date math moves onto the core recurrence helpers; the only source-specific
# code is the resolve-then-retrieve and _describe.

FEATURE_URL = "https://services-ap1.arcgis.com/1WJBRkF3v1EEG5gz/arcgis/rest/services/Waste_Collection_Date3/FeatureServer/0"

_SIX_WEEKLY = datetime.timedelta(weeks=6)
_from_ms = date_parsers.from_epoch(unit="ms")

_TYPE_MAP = {
    "Rubbish": wt.GENERAL_WASTE,
    "Green Waste": wt.GARDEN_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Street Sweeping": wt.OTHER,
}

_ARG = "property_location"

# EZI_ADDRESS is the Vicmap address string: upper case, no commas, street type
# spelled out, suburb then postcode ("266 GOWER STREET PRESTON 3072"). The
# lookup below is a prefix LIKE against it, so a comma, a "VIC", or an
# abbreviated street type matches nothing at all -- which is most of what
# visitors actually type.
_STREET_TYPES = {
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BVD": "BOULEVARD",
    "BLVD": "BOULEVARD",
    "CCT": "CIRCUIT",
    "CL": "CLOSE",
    "CR": "CRESCENT",
    "CRES": "CRESCENT",
    "CT": "COURT",
    "DR": "DRIVE",
    "ESP": "ESPLANADE",
    "GDNS": "GARDENS",
    "GR": "GROVE",
    "GRV": "GROVE",
    "HWY": "HIGHWAY",
    "LN": "LANE",
    "PDE": "PARADE",
    "PL": "PLACE",
    "RD": "ROAD",
    "SQ": "SQUARE",
    "ST": "STREET",
    "TCE": "TERRACE",
    "WY": "WAY",
}
_STATES = {"VIC", "VICTORIA"}

# Enough to show the visitor which property they meant, without pulling the
# whole municipality back when someone searches for a bare street name.
_MAX_SUGGESTIONS = 10


def _normalise(value: str) -> str:
    """Upper case, drop commas and collapse whitespace."""
    return " ".join(value.upper().replace(",", " ").split())


def _register_form(value: str) -> str:
    """What the visitor typed, written the way EZI_ADDRESS holds it."""
    words = [_STREET_TYPES.get(word, word) for word in _normalise(value).split()]
    while words and words[-1] in _STATES:
        words.pop()
    return " ".join(words)


def _prefixes(value: str) -> list[str]:
    """Progressively shorter prefixes of the address, longest first.

    EZI_ADDRESS ends with the suburb and postcode, and a visitor who gets
    either of those slightly wrong (or omits them) would otherwise match
    nothing. Shortening the prefix recovers the match; the caller still has to
    decide what to do when more than one property comes back.
    """
    address = _register_form(value)
    words = address.split()
    candidates = [address]
    # Trailing postcode, then the suburb one word at a time, never past the
    # street number and street name.
    if words and words[-1].isdigit() and len(words[-1]) == 4:
        words = words[:-1]
        candidates.append(" ".join(words))
    while len(words) > 2:
        words = words[:-1]
        candidates.append(" ".join(words))
    return list(dict.fromkeys(c for c in candidates if c))


def _resolve_object_id(property_location: str) -> Any:
    wanted = _register_form(property_location)
    for prefix in _prefixes(property_location):
        # ArcGIS `where` is SQL-ish, so a quote in the address (O'Hea Street)
        # would otherwise end the literal early.
        escaped = prefix.replace("'", "''")
        lookup = feature_query(
            FEATURE_URL,
            where=f"UPPER(EZI_ADDRESS) LIKE '{escaped}%'",
            out_fields="EZI_ADDRESS,OBJECTID",
            result_record_count=_MAX_SUGGESTIONS + 1,
        )
        features = ArcGisFeatureParser()(lookup)
        if not features:
            continue

        exact = [f for f in features if _normalise(f["EZI_ADDRESS"]) == wanted]
        if len(exact) == 1:
            return exact[0]["OBJECTID"]
        if len(features) == 1:
            return features[0]["OBJECTID"]

        raise SourceArgAmbiguousWithSuggestions(
            _ARG,
            property_location,
            [f["EZI_ADDRESS"] for f in features[:_MAX_SUGGESTIONS]],
        )

    raise SourceArgumentNotFound(
        _ARG,
        property_location,
        "Darebin holds addresses as street number, street name, suburb and "
        "postcode, for example '266 Gower Street PRESTON 3072'.",
    )


def _retrieve(source: BaseSource) -> Response:
    """Resolve the address to an OBJECTID, then fetch its schedule fields.

    A plain function (rather than :class:`~...ArcGis.ArcGisTwoStepFeatureRetriever`)
    because the shared retriever only tries one lookup and picks the first
    match unconditionally; this source instead retries with progressively
    shorter address prefixes and disambiguates with suggestions when a prefix
    matches more than one property.
    """
    property_location = source.params[_ARG]
    object_id = _resolve_object_id(property_location)
    response = feature_query(
        FEATURE_URL,
        where=f"OBJECTID={object_id}",
        out_fields="Collection_Day,Green_Collection,Recycle_Collection,Street_Sweeping",
    )
    if not response.json().get("features"):
        raise SourceArgumentNotFound(
            _ARG,
            property_location,
            "Darebin found the address but holds no collection details for it.",
        )
    return response


def _describe(attrs, source):
    collection_day = attrs["Collection_Day"]
    weekday = recurrence.WEEKDAYS[collection_day.lower()]

    # Rubbish — weekly from the next occurrence of the collection weekday.
    yield Schedule(
        "Rubbish",
        recurrence.most_recent_weekday(weekday),
        recurrence.WEEKLY,
        52,
        anchor=True,
    )
    # Green + Recycling — fortnightly from their epoch-ms base dates.
    yield Schedule(
        "Green Waste",
        _from_ms(attrs["Green_Collection"]),
        recurrence.FORTNIGHTLY,
        26,
        anchor=True,
    )
    yield Schedule(
        "Recycling",
        _from_ms(attrs["Recycle_Collection"]),
        recurrence.FORTNIGHTLY,
        26,
        anchor=True,
    )
    # Street sweeping — the next single date on a 6-week cycle.
    yield Schedule(
        "Street Sweeping",
        _from_ms(attrs["Street_Sweeping"]),
        _SIX_WEEKLY,
        1,
        anchor=True,
    )


@final
class Source(BaseSource):
    TITLE = "City of Darebin"
    DESCRIPTION = "Source for City of Darebin waste collection."
    URL = "https://www.darebin.vic.gov.au/"
    COUNTRY = "au"

    TEST_CASES: ClassVar[dict] = {
        "266 Gower Street PRESTON 3072": {
            "property_location": "266 Gower Street PRESTON 3072"
        },
        "23 EDWARDES STREET RESERVOIR 3073": {
            "property_location": "23 EDWARDES STREET RESERVOIR 3073"
        },
        # The shapes people type. The register holds none of them verbatim.
        "Comma separated with state": {
            "property_location": "266 Gower Street, Preston VIC 3072"
        },
        "Abbreviated street type": {"property_location": "266 Gower St Preston"},
    }

    PARAMS = (text_field("property_location", "Property Location"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full property location as it appears on the council site "
            "(e.g. '266 Gower Street PRESTON 3072')."
        ),
    }

    # Resolve the address to an OBJECTID ourselves (retrying with progressively
    # shorter prefixes and disambiguating with suggestions), then fetch that
    # feature's schedule fields through the shared primitives. staticmethod
    # keeps _retrieve's single-argument signature: an unwrapped plain function
    # assigned here would otherwise bind as a method and receive ``source``
    # twice, once from the descriptor and once from ``self.retrieve(self)``.
    retrieve = staticmethod(_retrieve)
    parse = ArcGisFeatureParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
