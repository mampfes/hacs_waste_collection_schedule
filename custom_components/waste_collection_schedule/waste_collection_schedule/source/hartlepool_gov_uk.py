from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    LookupStep,
)
from waste_collection_schedule.transformers import HtmlTransformer

_HOSTNAME = "online.hartlepool.gov.uk"


@final
class Source(BaseSource):
    TITLE = "Hartlepool Borough Council"
    DESCRIPTION = (
        "Source for www.hertlepool.gov.uk services for Hartlepool Borough Council."
    )
    URL = "https://www.hartlepool.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.FOOD_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100110021946"},
        "Test_002": {"uprn": "100110007383"},
        "Test_003": {"uprn": 10009716952},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering in your address details."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=f"https://{_HOSTNAME}/service/Refuse_and_recycling___check_bin_day",
        skip_landing_page=True,
        auth_test_url=f"https://{_HOSTNAME}/apibroker/domain/{_HOSTNAME}",
        steps=[
            LookupStep(
                "5ec67e019ffdd",
                form_values=lambda ctx, source: {
                    "collectionLocationUPRN": {"value": source.params["uprn"]}
                },
                no_retry="true",
            ),
        ],
    )
    # The schedule is an HTML fragment in one field: a <div> per collection
    # whose <span> reads "General Waste (green) 29/09/2026".
    parse = HtmlParser(
        "div span",
        from_json_key=(
            "integration",
            "transformed",
            "rows_data",
            "0",
            "HTMLCollectionDatesText",
        ),
    )
    transform = HtmlTransformer(
        date_getter=lambda span: span.get_text(strip=True).rsplit(" ", 1)[-1],
        type_getter=lambda span: span.get_text(strip=True).rsplit(" ", 1)[0],
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Food Waste (caddy)": wt.FOOD_WASTE,
            "General Waste (green)": wt.GENERAL_WASTE,
            "Recycling (grey)": wt.RECYCLABLES,
            "Garden Waste (brown)": wt.GARDEN_WASTE,
        },
    )
