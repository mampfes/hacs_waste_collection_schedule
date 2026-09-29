from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://mijn.circulus.nl"


def _registered(response, *, postal_code: str, house_number: str, **_) -> bool:
    """Registering the address opens the session the calendar is read in."""
    if not response.json().get("success"):
        raise SourceArgumentNotFound("postal_code", f"{postal_code} {house_number}")
    return True


def _window() -> dict[str, str]:
    today = date.today()
    return {
        "from": today.isoformat(),
        "till": (today + timedelta(days=365)).isoformat(),
    }


@final
class Source(BaseSource):
    TITLE = "Circulus"
    DESCRIPTION = "Source for circulus.nl waste collection."
    URL = "https://mijn.circulus.nl"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"postal_code": "7206AC", "house_number": "1"},
    }

    PARAMS = (postcode(postcode_field="postal_code", house_field="house_number"),)

    # The address is registered first: the calendar is served for the address
    # held in the session cookie that answer sets.
    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API_URL}/register/zipcode.json",
                method="POST",
                data=lambda postal_code, house_number, **_: {
                    "zipCode": postal_code,
                    "number": house_number,
                },
                pick=_registered,
            ),
        ),
        url=f"{_API_URL}/afvalkalender.json",
        params=lambda *_, **__: _window(),
        raise_for_status=True,
    )

    parse = JsonParser("customData", "response", "garbage")

    preprocess = ExplodeList("dates", into="date")

    transform = JsonTransformer(
        date_key="date",
        type_key="code",
        type_value_map={
            "REST": wt.GENERAL_WASTE,
            "GFT": wt.ORGANIC,
            "PAP": wt.PAPER,
            "PMD": wt.RECYCLABLES,
            "ZWAKRA": wt.RECYCLABLES,
        },
    )
