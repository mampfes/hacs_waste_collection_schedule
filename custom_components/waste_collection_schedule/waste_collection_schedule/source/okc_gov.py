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
# automatically if it errors or returns nothing, so a source-defined
# retrieve()/parse() expresses the two shapes and the fallback between them.

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


def _describe(record: tuple, source: Any):
    waste_type, payload = record
    today = datetime.date.today()

    # Unofficial feed: an explicit next date, no reconstruction required.
    if isinstance(payload, datetime.date):
        yield Schedule(waste_type, payload, count=1)
        return

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

    def _retrieve_unofficial(
        self, source: "Source", record_id: str
    ) -> "list[tuple[str, datetime.date]]":
        """Fetch the unofficial okc.schizo.dev feed as ``[(waste_type, date)]``.

        The endpoint returns explicit upcoming dates for trash, recycling and
        bulky waste keyed by a single recordID, so no weekday/biweekly
        reconstruction is needed; the reported weekday is used only when a
        section omits explicit dates.
        """
        response = source.session.get(UNOFFICIAL_URL, params={"recordID": record_id})
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise SourceArgumentNotFound(
                "recordID",
                record_id,
                "the unofficial source did not return valid JSON for this recordID.",
            ) from exc

        if not isinstance(data, dict):
            raise SourceArgumentNotFound(
                "recordID",
                record_id,
                "no schedule found for this recordID in the unofficial source.",
            )

        today = datetime.date.today()
        entries: list[tuple[str, datetime.date]] = []

        # Trash: single "next" pickup, optionally falling back to the weekday.
        trash = data.get("trash")
        if isinstance(trash, dict):
            trash_date: datetime.date | None = None
            raw_next = (trash.get("next") or {}).get("date")
            if raw_next:
                try:
                    parsed = datetime.datetime.strptime(
                        str(raw_next), "%Y-%m-%d"
                    ).date()
                    if parsed >= today:
                        trash_date = parsed
                except ValueError:
                    trash_date = None
            if trash_date is None and trash.get("day"):
                trash_date = _resolve_pickup_date(str(trash["day"]), today)
            if trash_date is not None:
                entries.append(("TRASH", trash_date))

        # Recycling: list of upcoming biweekly pickups.
        recycling = data.get("recycling")
        if isinstance(recycling, dict):
            recycle_date = _next_from_pickups(recycling.get("pickups"), today)
            if recycle_date is None and recycling.get("day"):
                recycle_date = _resolve_pickup_date(str(recycling["day"]), today)
            if recycle_date is not None:
                entries.append(("RECYCLE", recycle_date))

        # Bulky waste: list of upcoming monthly pickups.
        bulky = data.get("bulkyWaste")
        if isinstance(bulky, dict):
            bulky_date = _next_from_pickups(bulky.get("pickups"), today)
            if bulky_date is None and bulky.get("schedule"):
                bulky_date = _resolve_pickup_date(str(bulky["schedule"]), today)
            if bulky_date is not None:
                entries.append(("BULKY", bulky_date))

        return entries

    def _retrieve_official(self, source: "Source", object_ids: dict) -> dict:
        responses = {}
        for waste_type, object_id in object_ids.items():
            if not object_id:
                continue
            url, argument = WASTE_LAYERS[waste_type]
            retriever = ArcGisFeatureRetriever(url, where=f"OBJECTID={object_id}")
            responses[waste_type] = (retriever(source), argument, object_id)
        return responses

    def retrieve(self, source: "Source"):
        record_id = str(source.params.get("recordID") or "").strip()
        object_ids = {
            "TRASH": source.params.get("trashObjectID") or "",
            "RECYCLE": source.params.get("recycleObjectID") or "",
            "BULKY": source.params.get("bulkyObjectID") or "",
        }
        has_official = any(object_ids.values())

        if record_id:
            # Prefer the unofficial feed; fall back to the official OBJECTIDs
            # automatically if it errors or yields nothing and any are set.
            try:
                entries = self._retrieve_unofficial(source, record_id)
            except Exception:
                if not has_official:
                    raise
                entries = None
            if entries:
                return {"kind": "unofficial", "entries": entries}
            if not has_official:
                return {"kind": "unofficial", "entries": entries or []}

        return {
            "kind": "official",
            "responses": self._retrieve_official(source, object_ids),
        }

    def parse(self, raw, source: "Source | None" = None):
        if raw["kind"] == "unofficial":
            entries = raw["entries"]
            if not entries:
                record_id = str(source.params.get("recordID") if source else "") or ""
                raise SourceArgumentNotFound(
                    "recordID",
                    record_id,
                    "no upcoming collections found for this recordID in the "
                    "unofficial source.",
                )
            return list(entries)

        records = []
        for waste_type, (response, argument, object_id) in raw["responses"].items():
            features = ArcGisFeatureParser()(response, source)
            if not features:
                raise SourceArgumentNotFound(
                    argument,
                    object_id,
                    "no zone found with this OBJECTID in the OKC Open Data Portal.",
                )
            records.append((waste_type, features[0]))
        return records
