import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# City of Yarra publishes its collection zones on one MapServer with two
# layers: layer 1 (waste) carries the property's collection weekday and the
# anchor date that fixes its fortnightly recycling phase, layer 0 (glass)
# carries an independent anchor plus the glass cycle length in days. Both are
# point-in-polygon lookups from a single geocode, which is exactly what the
# shared multi-layer ArcGIS retriever does. The source-specific code validates
# those required fields, projects their recurrences, and applies the council's
# own public-holiday rule.

MAP_SERVER_URL = (
    "https://yccgis-prd.esriaustraliaonline.com.au/arcgis/rest/services/"
    "Waste_Services/CW_FC_PRD_Waste_Collection/MapServer"
)

GLASS_LAYER = "glass"
WASTE_LAYER = "waste"

# (label, feature_url, out_fields) per layer; the label is carried through to
# each parsed record so _describe() knows which fields it is looking at.
LAYERS = [
    (WASTE_LAYER, f"{MAP_SERVER_URL}/1", "collection_day,recycling_anchor_date"),
    (GLASS_LAYER, f"{MAP_SERVER_URL}/0", "anchor_date,frequency_days"),
]

# How many weekly collections to project; the fortnightly and glass cycles
# cover the same horizon at their own cadence.
WEEKS_AHEAD = 52

_TYPE_MAP = {
    "Rubbish": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Glass": wt.GLASS,
    "FOGO": wt.ORGANIC,
}


def _geocode_address(address: str) -> str:
    """Qualify the address so the world geocoder resolves it in Victoria."""
    return f"{address}, Victoria, Australia"


def _to_date(value: object) -> datetime.date | None:
    """Read an ArcGIS date field, which these layers publish as an ISO string."""
    if isinstance(value, str) and value:
        return datetime.date.fromisoformat(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.datetime.fromtimestamp(value / 1000, tz=datetime.UTC).date()
    return None


def _required_date(attrs: dict, field: str, layer: str) -> datetime.date:
    """Read a required provider date, failing instead of hiding a bin stream."""
    value = attrs.get(field)
    try:
        parsed = _to_date(value)
    except (OSError, OverflowError, ValueError) as err:
        raise ValueError(
            f"City of Yarra {layer} layer returned invalid {field}: {value!r}"
        ) from err
    if parsed is None:
        raise ValueError(f"City of Yarra {layer} layer did not return required {field}")
    return parsed


def _required_frequency(attrs: dict) -> int:
    """Read the required positive glass cadence published by the provider."""
    value = attrs.get("frequency_days")
    try:
        if isinstance(value, bool) or (
            isinstance(value, float) and not value.is_integer()
        ):
            raise ValueError
        frequency = int(value)
    except (TypeError, ValueError) as err:
        raise ValueError(
            f"City of Yarra glass layer returned invalid frequency_days: {value!r}"
        ) from err
    if frequency <= 0:
        raise ValueError(
            f"City of Yarra glass layer returned invalid frequency_days: {value!r}"
        )
    return frequency


def _is_delayed_collection_day(collection_date: datetime.date) -> bool:
    """Whether Yarra moves this scheduled collection forward by one day.

    Good Friday affects that Friday alone. Christmas delays cascade through
    the remaining weekday rounds: when Christmas is on a Monday, for example,
    every Monday-to-Friday round moves one day; when it is on a Thursday, both
    Thursday and Friday move. A weekend Christmas does not affect a weekday
    round.
    """
    if collection_date == recurrence.good_friday(collection_date.year):
        return True

    christmas = datetime.date(collection_date.year, 12, 25)
    if christmas.weekday() > 4:
        return False
    last_weekday = christmas + datetime.timedelta(days=4 - christmas.weekday())
    return christmas <= collection_date <= last_weekday


def _anchored_schedule(
    key: str,
    anchor: datetime.date,
    step: datetime.timedelta,
    count: int,
) -> Schedule:
    """Build a projection that retains yesterday when it shifts onto today.

    The shared recurrence expander normally starts on or after today. On the
    day after Good Friday or Christmas that would discard yesterday before the
    holiday stage can move it to today. Add that one in-phase occurrence back,
    reducing the ordinary projection by one so the published horizon stays the
    requested ``count``.
    """
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    shifted_today = (
        yesterday >= anchor
        and _is_delayed_collection_day(yesterday)
        and (yesterday - anchor) % step == datetime.timedelta(0)
    )
    extra = (yesterday,) if shifted_today else ()
    return Schedule(
        key,
        anchor,
        step,
        count - len(extra),
        anchor=True,
        extra=extra,
    )


def _describe(record, source):
    """Project a layer's matched feature into its Schedule descriptors.

    ``record`` is the ``(label, attrs)`` pair produced by
    :class:`ArcGisMultiFeatureParser`. Every schedule is anchored, so its
    historical start date is rolled forward to the first occurrence on or
    after today before the dates are generated.
    """
    label, attrs = record

    if label == WASTE_LAYER:
        collection_day = attrs.get("collection_day")
        weekday = recurrence.weekday(collection_day or "")
        if weekday is None:
            raise ValueError(
                "City of Yarra waste layer returned invalid collection_day: "
                f"{collection_day!r}"
            )

        # Rubbish and FOGO both run weekly on the property's collection day,
        # today's collection included when that day is today.
        start = recurrence.most_recent_weekday(weekday)
        yield _anchored_schedule("Rubbish", start, recurrence.WEEKLY, WEEKS_AHEAD)
        yield _anchored_schedule("FOGO", start, recurrence.WEEKLY, WEEKS_AHEAD)

        # Recycling alternates fortnightly between zones; the layer's anchor
        # date fixes this property's phase.
        recycling_anchor = _required_date(attrs, "recycling_anchor_date", WASTE_LAYER)
        yield _anchored_schedule(
            "Recycling",
            recycling_anchor,
            recurrence.FORTNIGHTLY,
            WEEKS_AHEAD // 2,
        )
        return

    if label != GLASS_LAYER:
        raise ValueError(f"City of Yarra returned unexpected layer label: {label!r}")

    # Glass runs on its own cycle (currently every 28 days) with an
    # independent per-polygon anchor and cycle length.
    glass_anchor = _required_date(attrs, "anchor_date", GLASS_LAYER)
    frequency = _required_frequency(attrs)
    yield _anchored_schedule(
        "Glass",
        glass_anchor,
        datetime.timedelta(days=frequency),
        WEEKS_AHEAD // 4,
    )


def _adjust(collection_date: datetime.date, key: str, source) -> datetime.date:
    """Council rule: collections run on every public holiday except Good
    Friday and Christmas Day, when they happen one day later."""
    if _is_delayed_collection_day(collection_date):
        return collection_date + datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "City of Yarra"
    DESCRIPTION = "Source for City of Yarra waste collection."
    URL = "https://www.yarracity.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@yeaaaaaahh"]

    TEST_CASES: ClassVar[dict] = {
        "Fitzroy Town Hall": {"address": "201 Napier Street, Fitzroy VIC 3065"},
        "Richmond Town Hall": {"address": "333 Bridge Road, Richmond VIC 3121"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address including suburb and postcode, "
            "e.g. '333 Bridge Road, Richmond VIC 3121'."
        ),
    }

    # Declarative pipeline: geocode once, spatially query both layers, tag each
    # response with its label, then project each match into concrete dates and
    # defer the two days the council does not collect on.
    retrieve = ArcGisMultiFeatureRetriever(
        LAYERS,
        address=_geocode_address,
        require_all=True,
    )
    parse = ArcGisMultiFeatureParser(
        first_per_layer=True,
        argument="address",
        hint="the address must be within the City of Yarra.",
    )
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
