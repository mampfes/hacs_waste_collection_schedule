from datetime import date, datetime, timedelta
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import RowTransformer

CALENDAR_PAGE_URL = (
    "https://poriruacity.govt.nz/services/rubbish-and-recycling/recycling-calendar/"
)

JS_URL = "https://storage.googleapis.com/pcc-static-v6/ALLJS/recycle-calendar/index.js"
_JS_LINK = r'src="(https://storage\.googleapis\.com/pcc-static-v6/[^"]*recycle-calendar/index\.js[^"]*)"'
_MAP_URL = "https://maps.poriruacity.govt.nz/server/rest/services/Property/PropertyAdminExternal/MapServer/5/query"


def _address(address):
    return address.replace(",", "", 1) if address.count(",") > 1 else address


def _query(target, context, address, **_):
    return {
        "where": f"lower(address) = '{_address(address).lower()}'",
        "f": "pjson",
        "outFields": "Address,OBJECTID,Collection_Day,Collection_Zone",
        "returnGeometry": "false",
        "resultRecordCount": 20,
        "orderByFields": "Address",
    }


def _collections(record, source):
    address = _address(source.params["address"]) if source is not None else ""
    data = record["address"]
    if "features" not in data or not data["features"]:
        raise SourceArgumentNotFound("address", address)
    properties = data["features"][0]["attributes"]
    today = date.today()
    next_day = next(
        (
            today + timedelta(days=i)
            for i in range(1, 8)
            if (today + timedelta(days=i)).strftime("%A")
            == properties["Collection_Day"]
        ),
        None,
    )
    if next_day is None:
        raise SourceArgumentNotFound("address", address)
    calendar = record["calendar"]
    zone = properties["Collection_Zone"].replace(" ", "").lower()
    anchor = datetime.strptime(calendar["zones"][zone][next_day.weekday()], "%Y-%m-%d")
    sequence = ["glass", "rubbish", "mixed", "rubbish"]
    rows = []
    for offset in (0, 7, 14):
        day = next_day + timedelta(days=offset)
        stamp = int(datetime(day.year, day.month, day.day).timestamp() * 1000)
        anchor_stamp = int(anchor.timestamp() * 1000)
        week = int(round((stamp - anchor_stamp) / 864e5) // 7)
        key = sequence[abs(week) % 4]
        rows.extend((day, label) for label in calendar["collections"][key])
    return rows


@final
class Source(BaseSource):
    TITLE = "Porirua City"
    DESCRIPTION = "Source for Porirua City."
    URL = "https://poriruacity.govt.nz/"
    COUNTRY = "nz"
    TEST_CASES: ClassVar[dict] = {
        "6 Ration Lane, Whitby, Porirua City 5024": {
            "address": "6 Ration Lane Whitby, Porirua City 5024"
        },
        "104 Main Road, Titahi Bay, Porirua City 5022": {
            "address": "104 Main Road Titahi Bay, Porirua City 5022"
        },
        "Address single-comma test": {
            "address": "104 Main Road Titahi Bay, Porirua City 5022"
        },
    }
    PARAMS = (street_address(),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.GLASS, wt.RECYCLABLES]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your address as shown at https://poriruacity.govt.nz/services/rubbish-and-recycling/recycling-calendar/. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.LinkedAssetRetriever(
            CALENDAR_PAGE_URL, pattern=_JS_LINK, fallback_url=JS_URL
        ),
        targets=lambda source, context: (_MAP_URL,),
        fetch=retrievers.Request(lambda target, context, **_: target, params=_query),
        include_prepared=True,
    )
    parse = parsers.NamedResponses(
        {
            "calendar": parsers.JsObjectParser(
                {
                    "zones": r"const\s?Xs\s?=\s?(\{.*?\});",
                    "collections": r"collections:\s?(\{(?:\w+:\s?\[.*?\],?)+\})",
                }
            ),
            "address": parsers.JsonParser(),
        }
    )
    preprocess = preprocessors.ExplodeList(_collections)
    transform = RowTransformer(
        type_value_map={
            "rubbish": wt.GENERAL_WASTE,
            "glass": wt.GLASS,
            "mixed": wt.RECYCLABLES,
        }
    )
