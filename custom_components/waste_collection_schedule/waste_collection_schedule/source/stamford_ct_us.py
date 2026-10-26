from typing import ClassVar, final

from waste_collection_schedule import preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.StamfordCalendar import (
    BASE_URL,
    CalendarParser,
    street_url,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "City of Stamford, CT"
    DESCRIPTION = (
        "Source for the City of Stamford, CT garbage and recycling pickup day lookup."
    )
    URL = "https://www.stamfordct.gov/government/operations/recycling-and-sanitation/about/recycling-and-garbage-schedule"
    COUNTRY = "us"
    TEST_CASES: ClassVar[dict] = {
        "Parker Ave": {"street": "Parker Ave"},
        "Washington Blvd, house 200": {
            "street": "Washington Blvd",
            "house_number": 200,
        },
        "Washington Blvd, house 500": {
            "street": "Washington Blvd",
            "house_number": 500,
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street": "zzzznotreal"},
        "Invalid house number": {"street": "Washington Blvd", "house_number": "abc"},
        "House number required": {"street": "Washington Blvd"},
    }
    PARAMS = (street(), house_number(optional=True))
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your street name without house number. Enter house_number separately when pickup days vary along the street; the error lists the available ranges. Both numbered ranges and the council's ALL designation are supported. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.Request(
        lambda detail, **_: detail,
        before=(
            retrievers.Lookup(
                BASE_URL + "StreetMultipleResults.asp",
                params=lambda street, **_: {
                    "STREET": street.strip(),
                    "CHECKED": "TRUE",
                },
                pick=street_url,
            ),
        ),
    )
    parse = CalendarParser()
    preprocess = preprocessors.WeekdayRecurrence(
        day="day", keys=lambda record: record["type"], count=26
    )
    transform = RowTransformer(
        type_value_map={"general": wt.GENERAL_WASTE, "recycling": wt.RECYCLABLES}
    )
