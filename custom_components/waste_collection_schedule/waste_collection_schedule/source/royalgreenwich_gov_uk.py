from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    street_address,
    text_field,
)
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.service.GreenwichCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Royal Borough Of Greenwich"
    DESCRIPTION = "Source for services from the Royal Borough Of Greenwich"
    URL = "https://www.royalgreenwich.gov.uk/"
    TEST_CASES: ClassVar[dict] = {
        "address": {"address": "25 - Tizzard Grove - London - SE3 9DH"},
        "houseNumber": {"post_code": "SE9 5AW", "house": "11"},
        "alternativeWeek": {"address": "32 - Glenlyon Road - London - SE9 1AJ"},
    }
    HOWTO: ClassVar[dict] = {
        "en": 'Using a browser, go to [royalgreenwich.gov.uk](https://www.royalgreenwich.gov.uk/info/200171/recycling_and_rubbish/100/find_your_bin_collection_day). Find the collection day and the first bold text in the message below the search bar (right after "At" and before ":") is your address, use it as-is.'
    }
    COUNTRY = "uk"
    PARAMS = (
        text_field("post_code", term=POSTCODE, optional=True),
        house_number("house", optional=True),
        street_address(optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
            "food": wt.FOOD_WASTE,
        },
    )
