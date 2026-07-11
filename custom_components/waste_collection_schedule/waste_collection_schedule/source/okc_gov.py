import datetime
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# City of Oklahoma City Open Data Portal: three independently-optional
# FeatureServer layers (trash / recycling / bulky), each queried by attribute
# (``where=OBJECTID=...``) rather than an address geocode+spatial lookup. Each
# layer publishes its cadence as free text on a PickupDay-like field: a bare
# weekday (weekly), an "Nth Weekday" ordinal (monthly -- the new
# recurrence.monthly_nth_weekday()), or an explicit date. Recycling runs
# fortnightly but the layer only reports a weekday, so an optional
# recycle_reference_date pins which week via the existing anchor-cadence
# support (Schedule(..., anchor=True)).

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
    "TRASH": GENERAL_WASTE,
    "RECYCLE": RECYCLABLES,
    "BULKY": BULKY_WASTE,
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


def _describe(record: tuple, source: Any):
    waste_type, attrs = record
    today = datetime.date.today()

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
    DESCRIPTION = "Source for the City of Oklahoma City Open Data Portal (ArcGIS) waste collection zones."
    URL = "https://www.okc.gov"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
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
            "Provide the OBJECTID of one or more of your collection zones from "
            "the OKC Open Data Portal (trashObjectID, recycleObjectID, "
            "bulkyObjectID). At least one is required. Open the FeatureServer "
            "layers linked in the documentation, use the Query page to locate "
            "the zone that covers your address, and read its OBJECTID. "
            "Recycling is collected every other week and the portal only "
            "reports the weekday, so also set recycle_reference_date to one "
            "date you know recycling was (or will be) collected to pin the "
            "correct week."
        ),
    }

    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(
        self,
        trashObjectID: str | int = "",
        recycleObjectID: str | int = "",
        bulkyObjectID: str | int = "",
        recycle_reference_date: str = "",
    ):
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

        if not (trash or recycle or bulky):
            raise SourceArgumentNotFound(
                "trashObjectID",
                "",
                "provide at least one of trashObjectID, recycleObjectID or bulkyObjectID.",
            )

        super().__init__(
            trashObjectID=trash,
            recycleObjectID=recycle,
            bulkyObjectID=bulky,
            recycle_reference_date=reference,
        )

    def retrieve(self, source: "Source"):
        record_ids = {
            "TRASH": source.params.get("trashObjectID") or "",
            "RECYCLE": source.params.get("recycleObjectID") or "",
            "BULKY": source.params.get("bulkyObjectID") or "",
        }
        responses = {}
        for waste_type, object_id in record_ids.items():
            if not object_id:
                continue
            url, argument = WASTE_LAYERS[waste_type]
            retriever = ArcGisFeatureRetriever(url, where=f"OBJECTID={object_id}")
            responses[waste_type] = (retriever(source), argument, object_id)
        return responses

    def parse(self, raw, source: "Source | None" = None):
        records = []
        for waste_type, (response, argument, object_id) in raw.items():
            features = ArcGisFeatureParser()(response, source)
            if not features:
                raise SourceArgumentNotFound(
                    argument,
                    object_id,
                    "no zone found with this OBJECTID in the OKC Open Data Portal.",
                )
            records.append((waste_type, features[0]))
        return records
