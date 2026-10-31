from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id, postcode
from waste_collection_schedule.service.DrupalServiceCalendar import (
    ServiceCalendarParser,
    calendar_route,
    calendar_url,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Wolverhampton City Council"
    DESCRIPTION = "Source for Wolverhampton City Council waste collection."
    URL = "https://www.wolverhampton.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "Test Case": {"postcode": "WV1 1RD", "uprn": "10094887108"}
    }
    COUNTRY = "uk"
    PARAMS = (postcode(), location_id("uprn"))
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.ORGANIC,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Enter the postcode and UPRN from the council's In Your Area property page. The source follows its View the calendar link and reads the dated calendar supplied by the council, including seasonal gaps. Only services listed for that property are returned. Types now use canonical, localised names; update filters and customisations using old labels."
    }
    retrieve = retrievers.Request(
        lambda page_url, route, **_: route,
        params=lambda *_, uprn, **__: {"uprn": str(uprn)},
        before=(
            retrievers.Lookup(
                lambda postcode, uprn, **_: (
                    "https://www.wolverhampton.gov.uk/find-my-nearest/"
                    + postcode.replace(" ", "").upper()
                    + "/"
                    + str(uprn)
                ),
                pick=calendar_url,
            ),
            retrievers.Lookup(lambda page_url, **_: page_url, pick=calendar_route),
        ),
    )
    parse = ServiceCalendarParser()
    transform = RowTransformer(
        type_value_map={
            "waste": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
            "food": wt.ORGANIC,
        }
    )
