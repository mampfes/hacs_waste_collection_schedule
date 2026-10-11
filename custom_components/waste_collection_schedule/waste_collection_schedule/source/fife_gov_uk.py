from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.VerintCloud import (
    VerintCloudRetriever,
    VerintStep,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Fife Council"
    DESCRIPTION = "Source for Fife Council."
    URL = "https://www.fife.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "SANDYHILL ROAD, ST ANDREWS": {"uprn": 320069186},
        "CERES ROAD, PITSCOTTIE": {"uprn": 320063641},
        "SHORE ROAD, BALMALCOLM": {"uprn": "320083539"},
        "CANMORE STREET, DUNFERMLINE": {"uprn": "320101510"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/.",
    }

    retrieve = VerintCloudRetriever(
        "https://fife.form.uk.empro.verintcloudservices.com/",
        form="bin_calendar",
        auth_path="api/citizen?preview=false&locale=en",
        steps=(
            VerintStep(
                "api/custom?action=powersuite_bin_calendar_collections"
                "&actionedby=bin_calendar&loadform=True&access=citizen&locale=en",
                data=lambda previous, uprn, **_: {"uprn": str(uprn)},
            ),
        ),
    )
    parse = parsers.JsonParser("data", "tab_collections")
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%A, %B %d, %Y"),
        type_value_map={
            "Landfill / Blue Bin": wt.GENERAL_WASTE,
            "Cans and Plastics / Green Bin": wt.RECYCLABLES,
            "Food and Garden Waste / Brown Bin": [wt.FOOD_WASTE, wt.GARDEN_WASTE],
            "Paper and Cardboard / Grey Bin": wt.PAPER,
        },
    )
