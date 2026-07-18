import datetime
from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import ALL_TYPES

# Standalone JSON-API source. The calendar endpoint takes the street_code +
# building_number plus a year/month window, computed live so the request always
# covers the next 12 months. Each record carries the date split across year/
# month/day integer fields and a German type label, so the transformer builds the
# date and resolves the label onto a canonical WasteType.

API_URL = "https://www.awbkoeln.de/api/calendar"


def _calendar_params(street_code, building_number, **_):
    now = datetime.datetime.now()
    return {
        "street_code": street_code,
        "building_number": building_number,
        "start_year": now.year,
        "start_month": now.month,
        "end_year": now.year + 1,
        "end_month": now.month,
    }


@final
class Source(BaseSource):
    TITLE = "AWB Köln"
    DESCRIPTION = "Source for Abfallwirtschaftsbetriebe Köln waste collection."
    URL = "https://www.awbkoeln.de"
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = list(ALL_TYPES)

    TEST_CASES: ClassVar[dict] = {"Koeln": {"street_code": 2, "building_number": 50}}

    PARAMS = (
        text_field("street_code", label="Straßencode"),
        text_field("building_number", label="Hausnummer"),
    )

    retrieve = retrievers.HttpGetRetriever(url=API_URL, params=_calendar_params)
    parse = JsonParser("data")
    transform = JsonTransformer(
        date_key=lambda r: datetime.date(
            year=r["year"], month=r["month"], day=r["day"]
        ),
        type_key="type",
    )

    def __init__(self, street_code, building_number):
        super().__init__(street_code=street_code, building_number=building_number)
