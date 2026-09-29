from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

API = "https://wastecollections.haringey.gov.uk/api"
COUNCIL_ID = "45"

_TYPE_MAP = {
    "Non-Recyclable Waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Food Waste": wt.FOOD_WASTE,
    "Garden Waste": wt.GARDEN_WASTE,
}


def _padded_uprn(uprn, **_) -> str:
    return str(uprn).zfill(12)


def _pick_point_id(response, *keys, uprn, **_) -> str:
    """The lookup answers ``{"data": [{"id": <point id>, ...}]}``."""
    addresses = response.json().get("data") or []
    if not addresses:
        raise SourceArgumentNotFound("uprn", _padded_uprn(uprn))
    return addresses[0]["id"]


def _label(record) -> str:
    return record.get("taskTypeName") or record.get("serviceName") or ""


@final
class Source(BaseSource):
    TITLE = "Haringey Council"
    DESCRIPTION = "Source for haringey.gov.uk services for Haringey Council, UK."
    URL = "https://www.haringey.gov.uk/"
    COUNTRY = "uk"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@marcjay"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100021209182"},
        "Test_002": {"uprn": "100021207181"},
        "Test_003": {"uprn": "100021202738"},
        "Test_004": {"uprn": 100021202131},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your UPRN (available from "
            "[FindMyAddress.co.uk](https://www.findmyaddress.co.uk/))."
        ),
    }

    retrieve = retrievers.Request(
        f"{API}/getCollectionDays",
        method="POST",
        json=lambda point_id, **_: {
            "pointId": point_id,
            "pointType": "PointAddress",
            "councilId": COUNCIL_ID,
        },
        before=(
            retrievers.Lookup(
                f"{API}/getAddressByPointId",
                method="POST",
                json=lambda **params: {
                    "pointId": _padded_uprn(**params),
                    "councilId": COUNCIL_ID,
                    "pointType": "PointAddress",
                },
                pick=_pick_point_id,
            ),
        ),
    )

    parse = parsers.JsonParser("activeServices")

    preprocess = Compose(ExplodeList("serviceSchedules", into="schedule"))

    transform = JsonTransformer(
        date_key=lambda record: record["schedule"].get("currentScheduledDate"),
        type_key=_label,
        type_value_map=_TYPE_MAP,
        skip_unparseable_dates=True,
    )
