import datetime
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import Lookup, Request
from waste_collection_schedule.transformers import ICSTransformer

API = "https://www.ccc.tas.gov.au/wp-json/waste-collection"
DATE_REGEX = r"\d{1,2}/\d{1,2}/\d{4}"
WEEKS_TO_CHECK = 52

_SERVICES = {
    "Garbage Pickup": "Rubbish",
    "Recycling Pickup": "Recycling",
    "Green Waste Pickup": "Greenwaste",
}


def _formatted_address(response: Any, *_: Any, address: str, **__: Any) -> str:
    """The council's own spelling of the first address the search found."""
    data = response.json()
    if not data.get("success") or not data.get("results"):
        raise SourceArgumentNotFound("address", address)
    return data["results"][0]


def _describe(record: dict, source: Any):
    """A recurring schedule from the two next dates the council publishes.

    Hardwaste is left out on purpose: the council no longer collects it.
    """
    key = _SERVICES.get(record.get("name"))
    if key is None:
        return
    dates = re.findall(DATE_REGEX, record["value"])
    # Anything but two dates means the API has changed.
    if len(dates) != 2:
        raise ValueError("Data has changed, api processor needs to be updated")
    first, second = (
        datetime.datetime.strptime(value, "%d/%m/%Y").date() for value in dates
    )
    # The two published dates and WEEKS_TO_CHECK further ones at the same interval.
    yield Schedule(key, first, second - first, WEEKS_TO_CHECK + 2)


@final
class Source(BaseSource):
    TITLE = "Clarence City Council"
    DESCRIPTION = "The greater Eastern Shore of Hobart"
    URL = "https://www.ccc.tas.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "80 Clarence St": {"address": "80 Clarence St"},
        "5 Cambridge Road": {"address": "5 Cambridge Road"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address, e.g. `123 Clarence St`; the council's address search picks the first match.",
    }

    retrieve = Request(
        f"{API}/collection-search",
        method="POST",
        json=lambda key, **_: {"address": key},
        before=(
            Lookup(
                f"{API}/address-search",
                method="POST",
                json=lambda address, **_: {"address": address},
                pick=_formatted_address,
            ),
        ),
    )
    parse = parsers.JsonParser("results")
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Greenwaste": wt.GARDEN_WASTE,
        }
    )
