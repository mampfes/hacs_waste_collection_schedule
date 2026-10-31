from typing import ClassVar, final

from waste_collection_schedule import preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street, text_field
from waste_collection_schedule.service.SunshineCoast import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Sunshine Coast Queensland (QLD)"
    DESCRIPTION = "Source script for Sunshine Coast Queensland (QLD)."
    COUNTRY = "au"
    URL = "https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days"
    TEST_CASES: ClassVar[dict] = {
        "Hospital Rd": {"street_name": "hospital rd"},
        "Great Keppel Way": {"street_name": "great keppel way"},
        "House number and suburb": {"street_name": "12 Hospital Rd, Nambour"},
        "Street type spelled out": {"street_name": "hospital road"},
        "Street in several suburbs": {"street_name": "Main St", "locality": "Eumundi"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street_name": "zzzznotreal"},
        "Ambiguous suburb": {"street_name": "Main St"},
        "Unknown locality": {"street_name": "hospital rd", "locality": "zzzznotreal"},
    }
    PARAMS = (street("street_name"), text_field("locality", "Suburb", optional=True))
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    HOWTO: ClassVar[dict] = {
        "en": "Enter the street name as shown by the council's bin checker. House numbers, a comma-separated suburb and spelled-out street types are accepted. Use locality when a street occurs in several suburbs. The current published widget supplies the week-cycle anchor; the API supplies your street's weekday and week. Collections happening today are included. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = CalendarRetriever(
        "https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days",
        "https://www.sunshinecoast.qld.gov.au/__server__/api/v1",
    )
    parse = CalendarParser()
    preprocess = preprocessors.Compose(
        preprocessors.RecurrenceExpander(lambda schedule, _: (schedule,)),
        preprocessors.SortRows(),
    )
    transform = RowTransformer(
        type_value_map={
            "general": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
        }
    )
