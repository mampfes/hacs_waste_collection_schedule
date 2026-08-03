import datetime
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import FirstNonEmptyBranch, LabelledSections
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import (
    Branch,
    FallbackRetriever,
    HttpGetRetriever,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# City of Oklahoma City. Two independent feeds cover the same three waste types
# (trash / recycling / bulky):
#
# * the unofficial okc.schizo.dev API, keyed by a single ``recordID``, which
#   returns explicit upcoming dates (no reconstruction needed); and
# * the official Open Data Portal FeatureServer layers, each queried by
#   attribute (``where=OBJECTID=...``) and publishing its cadence as free text
#   on a PickupDay-like field: a bare weekday (weekly), an "Nth Weekday"
#   ordinal (monthly -- recurrence.monthly_nth_weekday()), or an explicit date.
#   Recycling runs fortnightly but the layer only reports a weekday, so an
#   optional recycle_reference_date pins which week via the anchor-cadence
#   support (Schedule(..., anchor=True)).
#
# ``recordID`` is preferred when set and falls back to the official OBJECTIDs
# automatically if it errors or returns nothing. That is a FallbackRetriever of
# two Branches read by a FirstNonEmptyBranch parser: each feed brings its own
# parser, and the official layers are only queried when the unofficial feed did
# not answer.

# Unofficial community API (single recordID covers trash, recycling and bulky).
UNOFFICIAL_URL = "https://okc.schizo.dev/trash"

TRASH_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/45426e5e1b31489db9afea603870f724/rest/services/OpenData/Utilities/FeatureServer/1"
RECYCLE_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/0f286e1243ca4bb39a70e323b1608222/rest/services/OpenData/Utilities/FeatureServer/3"
BULKY_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/c4455716f4bf4d1dafe6806e0e619de8/rest/services/OpenData/Utilities/FeatureServer/2"

# Waste type -> (FeatureServer layer URL, constructor argument name)
WASTE_LAYERS = {
    "TRASH": (TRASH_ZONES_URL, "trashObjectID"),
    "RECYCLE": (RECYCLE_ZONES_URL, "recycleObjectID"),
    "BULKY": (BULKY_ZONES_URL, "bulkyObjectID"),
}

_TYPE_MAP = {
    "TRASH": wt.GENERAL_WASTE,
    "RECYCLE": wt.RECYCLABLES,
    "BULKY": wt.BULKY_WASTE,
}

# The unofficial feed answers with one object per round, keyed by field name.
# Its labels are tagged so _describe can tell a feed section from a set of
# ArcGIS layer attributes: the two branches produce the same (label, payload)
# shape but say entirely different things inside the payload.
_UNOFFICIAL_SECTIONS = {
    "trash": ("unofficial", "TRASH"),
    "recycling": ("unofficial", "RECYCLE"),
    "bulkyWaste": ("unofficial", "BULKY"),
}

# Where each round states its next collection, in the order the feed prefers.
# Trash publishes a single "next" object; recycling and bulky publish a list of
# upcoming pickups. All three fall back to the free-text rule they report, which
# is a weekday for trash and recycling and an ordinal for bulky.
_UNOFFICIAL_DATES = {
    "TRASH": ("next", "day"),
    "RECYCLE": ("pickups", "day"),
    "BULKY": ("pickups", "schedule"),
}

_ORDINAL_RE = re.compile(
    r"^(?P<nth>[1-5])(st|nd|rd|th)\s+"
    r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)$"
)
_EXPLICIT_DATE_FORMATS = ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d")


def _resolve_pickup_date(pickup_rule: str, today: datetime.date) -> datetime.date:
    """Turn a layer's free-text pickup rule into the next collection date."""
    normalized = pickup_rule.strip()
    lower = normalized.lower()

    weekday = recurrence.weekday(lower)
    if weekday is not None:
        return recurrence.next_weekday(weekday, on_or_after=today)

    ordinal_match = _ORDINAL_RE.match(lower)
    if ordinal_match:
        nth = int(ordinal_match.group("nth"))
        weekday = recurrence.weekday(ordinal_match.group("weekday"))
        assert weekday is not None  # the regex only matches known weekday names
        return recurrence.monthly_nth_weekday(weekday, nth, on_or_after=today)

    for date_format in _EXPLICIT_DATE_FORMATS:
        try:
            return datetime.datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Unsupported pickup rule returned by API: '{pickup_rule}'")


def _next_from_pickups(pickups, today: datetime.date) -> "datetime.date | None":
    """First upcoming date from an unofficial-feed list of ``{"date": ...}``."""
    for pickup in pickups or []:
        if not isinstance(pickup, dict):
            continue
        raw = pickup.get("date")
        if not raw:
            continue
        try:
            parsed = datetime.datetime.strptime(str(raw), "%Y-%m-%d").date()
        except ValueError:
            continue
        if parsed >= today:
            return parsed
    return None


def _unofficial_date(
    waste_type: str, section: dict, today: datetime.date
) -> "datetime.date | None":
    """The next collection a feed section states, explicit dates first."""
    explicit, rule_field = _UNOFFICIAL_DATES[waste_type]

    if explicit == "next":
        raw = (section.get("next") or {}).get("date")
        if raw:
            try:
                parsed = datetime.datetime.strptime(str(raw), "%Y-%m-%d").date()
            except ValueError:
                parsed = None
            if parsed is not None and parsed >= today:
                return parsed
    else:
        from_pickups = _next_from_pickups(section.get(explicit), today)
        if from_pickups is not None:
            return from_pickups

    rule = section.get(rule_field)
    return _resolve_pickup_date(str(rule), today) if rule else None


def _has_record_id(**params: Any) -> bool:
    return bool(str(params.get("recordID") or "").strip())


def _has_object_ids(**params: Any) -> bool:
    return any(
        str(params.get(argument) or "").strip() for _, argument in WASTE_LAYERS.values()
    )


def _object_id_where(label: Any, **params: Any) -> "str | None":
    """This layer's attribute filter, or None when its OBJECTID is not set."""
    object_id = str(params.get(WASTE_LAYERS[label][1]) or "").strip()
    return f"OBJECTID={object_id}" if object_id else None


def _describe(record: tuple, source: Any):
    label, payload = record
    today = datetime.date.today()

    # Unofficial feed: explicit upcoming dates, no reconstruction required.
    if isinstance(label, tuple):
        waste_type = label[1]
        if not isinstance(payload, dict):
            return
        pickup_date = _unofficial_date(waste_type, payload, today)
        if pickup_date is not None:
            yield Schedule(waste_type, pickup_date, count=1)
        return

    waste_type = label
    attrs = payload
    if waste_type == "RECYCLE":
        raw_reference = source.params.get("recycle_reference_date")
        if raw_reference:
            reference = datetime.datetime.strptime(raw_reference, "%Y-%m-%d").date()
            yield Schedule("RECYCLE", reference, recurrence.FORTNIGHTLY, anchor=True)
            return

    pickup_day = None
    for field_name in ("PickupDay", "PickUpDay", "PICKUPDAY"):
        value = attrs.get(field_name)
        if value:
            pickup_day = str(value).strip()
            break
    if not pickup_day:
        return

    yield Schedule(waste_type, _resolve_pickup_date(pickup_day, today), count=1)


@final
class Source(BaseSource):
    TITLE = "City of Oklahoma City"
    DESCRIPTION = "Source for the City of Oklahoma City waste collection schedule. Supports the unofficial okc.schizo.dev API (single recordID) and the official OKC Open Data Portal (ArcGIS) waste collection zones."
    URL = "https://www.okc.gov"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Unofficial (schizo.dev) recordID": {
            "recordID": "1781503",
        },
        "Trash Fri / Recycle Mon / Bulky 4th Mon": {
            "trashObjectID": 1,
            "recycleObjectID": 1215,
            "bulkyObjectID": 1,
        },
        "Recycle every other week (anchored)": {
            "recycleObjectID": 1215,
            "recycle_reference_date": "2026-06-15",
        },
        "Recycle Fri every other week (anchored, live zone)": {
            "recycleObjectID": 1366,
            "recycle_reference_date": "2026-06-19",
        },
        "Trash only": {
            "trashObjectID": 2,
        },
    }

    PARAMS = (
        text_field("recordID", "Record ID (okc.schizo.dev)", optional=True),
        text_field("trashObjectID", "Trash Zone OBJECTID", optional=True),
        text_field("recycleObjectID", "Recycling Zone OBJECTID", optional=True),
        text_field("bulkyObjectID", "Bulky Waste Zone OBJECTID", optional=True),
        text_field(
            "recycle_reference_date",
            "Known Recycling Pickup Date (YYYY-MM-DD)",
            optional=True,
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Recommended: go to https://okc.schizo.dev , type in your address, "
            "and copy the record ID it shows into recordID. That single ID "
            "covers trash, recycling and bulky waste. If your address isn't "
            "found, try variations (e.g. drop a leading 'N'/'North'). "
            "Alternatively, use the official OKC data portals to find one "
            "OBJECTID per waste type (trashObjectID, recycleObjectID, "
            "bulkyObjectID): open the FeatureServer layer for the waste type, "
            "zoom into your house, click your zone and read the OBJECTID from "
            "the info popup. With the official method, recycling is collected "
            "every other week and the portal only reports the weekday, so also "
            "set recycle_reference_date to one date you know recycling was (or "
            "will be) collected to pin the correct week. If both recordID and "
            "official OBJECTIDs are provided, the unofficial recordID source is "
            "used first and falls back to the official OBJECTIDs if it fails or "
            "returns nothing."
        ),
    }

    retrieve = FallbackRetriever(
        Branch(
            "unofficial",
            HttpGetRetriever(
                UNOFFICIAL_URL, params=lambda **p: {"recordID": p["recordID"]}
            ),
            when=_has_record_id,
        ),
        Branch(
            "official",
            ArcGisMultiFeatureRetriever(
                [(label, url) for label, (url, _) in WASTE_LAYERS.items()],
                address=None,
                where=_object_id_where,
            ),
            when=_has_object_ids,
        ),
    )

    parse = FirstNonEmptyBranch(
        {
            "unofficial": LabelledSections(
                _UNOFFICIAL_SECTIONS,
                argument="recordID",
                hint="no schedule found for this recordID in the unofficial source.",
            ),
            "official": ArcGisMultiFeatureParser(
                first_per_layer=True,
                argument=lambda label: WASTE_LAYERS[label][1],
                hint="no zone found with this OBJECTID in the OKC Open Data Portal.",
            ),
        }
    )

    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(
        self,
        recordID: str | int = "",
        trashObjectID: str | int = "",
        recycleObjectID: str | int = "",
        bulkyObjectID: str | int = "",
        recycle_reference_date: str = "",
    ):
        record = str(recordID).strip()
        trash = str(trashObjectID).strip()
        recycle = str(recycleObjectID).strip()
        bulky = str(bulkyObjectID).strip()
        reference = str(recycle_reference_date).strip()

        if reference:
            try:
                datetime.datetime.strptime(reference, "%Y-%m-%d")
            except ValueError as exc:
                raise SourceArgumentNotFound(
                    "recycle_reference_date",
                    recycle_reference_date,
                    "must be an ISO date (YYYY-MM-DD) of a known recycling pickup.",
                ) from exc

        if not (record or trash or recycle or bulky):
            raise SourceArgumentNotFound(
                "recordID",
                "",
                "provide recordID (unofficial source) or at least one of "
                "trashObjectID, recycleObjectID or bulkyObjectID (official source).",
            )

        super().__init__(
            recordID=record,
            trashObjectID=trash,
            recycleObjectID=recycle,
            bulkyObjectID=bulky,
            recycle_reference_date=reference,
        )
