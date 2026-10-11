import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.JaduApiserver import rpc
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Refuse": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden": wt.GARDEN_WASTE,
}


def _iso_date(value) -> datetime.date | None:
    """The date of an ``YYYY-MM-DD`` field; an empty one has no collection."""
    return datetime.date.fromisoformat(value) if value else None


@final
class Source(BaseSource):
    TITLE = "South Holland District Council"
    DESCRIPTION = "Source for South Holland District Council."
    URL = "https://www.sholland.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "10002546801": {"uprn": 10002546801, "postcode": "PE11 2FR"},
        "PE12 7AR": {"uprn": "100030897036", "postcode": "PE12 7AR"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/. The postcode is "
            "not used by the council's lookup but is kept for existing "
            "configurations."
        ),
    }

    retrieve = rpc(
        "https://www.sholland.gov.uk/apiserver/ajaxlibrary",
        "SouthHolland.Waste.getCollectionDaysAjax",
        lambda uprn, **_: {"UPRN": str(uprn)},
        headers={"Referer": "https://www.sholland.gov.uk/mycollections"},
    )
    parse = parsers.JsonParser("result")
    # One field per round, each holding that round's next date.
    preprocess = preprocessors.DateFields(
        fields={
            "nextRefuseDate": "Refuse",
            "nextRecyclingDate": "Recycling",
            "nextGardenDate": "Garden",
        },
        parse_date=_iso_date,
    )
    transform = RowTransformer(type_value_map=_TYPE_MAP)
