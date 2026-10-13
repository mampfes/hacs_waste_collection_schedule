from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, text_field
from waste_collection_schedule.field_terms import POSTCODE, UPRN
from waste_collection_schedule.regions import Region
from waste_collection_schedule.service.EnvironmentFirstCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Environment First"
    URL = "https://environmentfirst.co.uk"
    DESCRIPTION = "Consolidated source for waste collection services from:\n        Eastbourne Borough Council\n        Lewes District Council\n        "
    TEST_CASES: ClassVar[dict] = {
        "houseUPRN": {"uprn": "100060063421"},
        "houseNumber": {"post_code": "BN228SG", "number": 3},
        "houseName": {"post_code": "BN73LG", "number": "Garden Cottage"},
    }
    COUNTRY = "uk"
    REGIONS = (
        Region(
            title="Eastbourne Borough Council",
            params={},
            url="https://lewes-eastbourne.gov.uk",
        ),
        Region(
            title="Lewes District Council",
            params={},
            url="https://lewes-eastbourne.gov.uk",
        ),
    )
    PARAMS = (
        text_field("post_code", term=POSTCODE, optional=True),
        house_number("number", optional=True),
        text_field("name", "Property name", optional=True),
        text_field("uprn", term=UPRN, optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "RUBBISH": wt.GENERAL_WASTE,
            "RECYCLING": wt.RECYCLABLES,
            "GARDEN WASTE": wt.GARDEN_WASTE,
        },
    )
