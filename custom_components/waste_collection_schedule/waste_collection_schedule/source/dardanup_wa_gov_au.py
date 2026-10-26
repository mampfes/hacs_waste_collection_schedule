from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    street,
    text_field,
)
from waste_collection_schedule.service.DardanupCalendar import (
    AREAS,
    CalendarParser,
    guide_urls,
)
from waste_collection_schedule.transformers import RowTransformer

_PAGE = "https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/find-your-bin-day.aspx"


@final
class Source(BaseSource):
    TITLE = "Shire of Dardanup"
    DESCRIPTION = "Source for Shire of Dardanup (WA) waste collection."
    URL = "https://www.dardanup.wa.gov.au"
    COUNTRY = "au"
    TEST_CASES: ClassVar[dict] = {
        "Hale Street (Area 1, Tuesday)": {
            "street": "Hale Street",
            "service_area": "Area 1",
        },
        "Hale Street Area 2": {"street": "Hale Street", "service_area": "Area 2"},
        "Burekup": {"street": "Burekup", "service_area": "Dardanup and Burekup"},
        "Dardanup West via collection_day": {
            "collection_day": "Monday",
            "service_area": "Dardanup and Burekup",
        },
        "Ash Court inferred area": {"street": "Ash Court"},
        "Rural Picton East": {"street": "Picton East", "service_area": "Rural Area 1"},
        "Rural Ferguson Valley split weekdays": {
            "street": "Ferguson Valley",
            "service_area": "Rural Area 2",
        },
        "Rural Crooked Brook": {
            "street": "Crooked Brook",
            "service_area": "Rural Area 2",
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Ambiguous Hale Street": {"street": "Hale Street"},
        "Legacy parity needs area": {
            "collection_day": "Monday",
            "recycling_in_even_week": True,
        },
        "Unknown weekday": {"service_area": "Area 1", "collection_day": "Saturday"},
    }
    PARAMS = (
        street(optional=True),
        dropdown("service_area", list(AREAS), optional=True),
        text_field("collection_day", "Collection weekday", optional=True),
    )
    WASTE_TYPES: ClassVar[list] = [wt.ORGANIC, wt.RECYCLABLES, wt.GENERAL_WASTE]
    HOWTO: ClassVar[dict] = {
        "en": "Find your street/townsite and service area in the current waste guide linked from https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/find-your-bin-day.aspx. Enter street and service_area; collection_day can specify the published weekday directly. Streets spanning Area 1 and Area 2 require service_area. Replace the old recycling_in_even_week argument with service_area: the published calendar now supplies the recycling phase and holiday replacements, including across ISO week 53. Rural two-bin services have no FOGO collection. Dates stop at the end of the published guide, with no projection beyond it. Since the v3 migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Request(_PAGE),
        targets=guide_urls,
        fetch=retrievers.Request(lambda url, response, **_: url),
        include_prepared=True,
    )
    parse = CalendarParser()
    transform = RowTransformer(
        type_value_map={
            "organic": wt.ORGANIC,
            "general": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
        }
    )
