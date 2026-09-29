import json
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = (
    "https://www.renfrewshire.gov.uk/bins-and-recycling/bin-collection/"
    "bin-collection-calendar/check-your-bin-collection-day/view/"
)


def _rounds(script, source) -> list:
    """(date, colour) rows from the calendar JSON embedded in the page.

    The JSON maps each date to the council's bins, an empty one being ``null``.
    """
    calendar = json.loads(script.string)
    return [
        (date.fromisoformat(day), bin_["ShortName"])
        for day, bins in calendar.items()
        for bin_ in bins.values()
        if bin_ is not None
    ]


@final
class Source(BaseSource):
    TITLE = "Renfrewshire Council"
    DESCRIPTION = "Source for renfrewshire.gov.uk services for Renfrewshire"
    URL = "https://renfrewshire.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "PA12 4JU", "uprn": "123033059"},
        "Test_002": {"postcode": "PA12 4AJ", "uprn": "123034174"},
        "Test_003": {"postcode": "PA2 9JB", "uprn": "123046497"},
    }

    PARAMS = (uprn(),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.GLASS,
        wt.PAPER,
    ]

    retrieve = HttpGetRetriever(url=lambda uprn, **_: f"{_API_URL}{uprn}")
    parse = HtmlParser("script#collections-data", require=["script#collections-data"])
    preprocess = ExplodeList(_rounds)
    transform = ICSTransformer(
        type_value_map={
            "Grey": wt.GENERAL_WASTE,
            "Brown": wt.ORGANIC,
            "Green": wt.GLASS,
            "Blue": wt.PAPER,
        }
    )
