import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://www.durham.gov.uk/apiserver/ajaxlibrary/"
_NS = {
    "jobs": "http://www.bartec-systems.com/Jobs_Get.xsd",
    "b": "http://www.bartec-systems.com",
}
# "Empty Bin Refuse 240L" -> "Refuse"
_BIN = re.compile(r"^Empty Bin\s+|\s+\d+\s*L$", re.IGNORECASE)


def _start(job) -> str:
    return (job.findtext("jobs:ScheduledStart", namespaces=_NS) or "")[:10]


@final
class Source(BaseSource):
    TITLE = "Durham County Council"
    DESCRIPTION = "Source for Durham County Council, UK."
    URL = "https://durham.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100110414978"},
        "Test_002": {"uprn": 100110427200},
    }

    PARAMS = (uprn(),)

    # A JSON-RPC call whose result is Bartec's SOAP Jobs_Get reply, holding
    # every job for the property back to when it was first scheduled.
    retrieve = HttpPostRetriever(
        url=_API_URL,
        json=lambda uprn, **_: {
            "jsonrpc": "2.0",
            "method": "durham.Localities.GetBartecCalendar",
            "params": {"uprn": str(uprn)},
            "id": "21",
            "name": "V2 AJAX End Point Library Worker",
        },
        headers=lambda uprn, **_: {
            "Referer": f"https://www.durham.gov.uk/bincollections?uprn={uprn}",
        },
    )
    parse = parsers.XmlParser(".//jobs:Job", namespaces=_NS, from_json_key="result")
    preprocess = preprocessors.RowFilter(
        lambda job, _: _start(job) >= datetime.date.today().isoformat()
    )
    transform = JsonTransformer(
        date_key=_start,
        type_key=lambda job: job.findtext("b:Name", namespaces=_NS) or "",
        clean=lambda name: _BIN.sub("", name),
        type_value_map={
            "refuse": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "organic": wt.GARDEN_WASTE,
            "food": wt.FOOD_WASTE,
            "clinical": wt.HAZARDOUS,
            "clinical waste sacks": wt.HAZARDOUS,
        },
    )
