from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import DateFields
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://refusecalendarapi.denbighshire.gov.uk"


@final
class Source(BaseSource):
    TITLE = "Denbighshire County Council"
    DESCRIPTION = "Source for Denbighshire County Council."
    URL = "https://www.denbighshire.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "10003928409": {"uprn": "10003928409"},
        "100100183412": {"uprn": 100100183412},
        "10003928445": {"uprn": "10003928445"},
    }

    PARAMS = (uprn(),)

    # The calendar answers only with a fresh CSRF token in the header.
    retrieve = retrievers.Request(
        lambda csrf_token, uprn, **_: f"{_API_URL}/Calendar/{uprn}",
        headers=lambda csrf_token, **_: {"X-CSRF-TOKEN": csrf_token},
        before=(
            retrievers.Lookup(
                f"{_API_URL}/Csrf/token",
                pick=lambda response, **_: response.json()["token"],
            ),
        ),
    )
    # One object per property, with a date field per round (empty when the
    # property has no such round). Food is collected with the recycling.
    parse = parsers.JsonParser()
    preprocess = DateFields(
        fields={
            "refuseDate": "Refuse",
            "recyclingDate": "Recycling",
            "gardenDate": "Garden",
            "ahpDate": "AHP",
        },
        parse_date=lambda value: (
            date_parsers.for_format("%d/%m/%Y")(value) if value else None
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": [wt.RECYCLABLES, wt.FOOD_WASTE],
            "Garden": wt.GARDEN_WASTE,
            "AHP": wt.OTHER,
        }
    )
