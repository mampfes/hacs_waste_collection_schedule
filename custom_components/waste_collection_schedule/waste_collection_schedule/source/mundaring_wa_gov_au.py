from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, text_field
from waste_collection_schedule.service.MundaringBinCalendar import (
    CalendarParser,
    calendar_retriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Shire of Mundaring"
    DESCRIPTION = "Source for mundaring.wa.gov.au services for the Shire of Mundaring, Western Australia"
    URL = "https://www.mundaring.wa.gov.au/"
    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"parcel_number": 103239, "suburb": "Helena Valley"},
        "Test_002": {"parcel_number": "100119", "suburb": "Swan View"},
        "Test_003": {"parcel_number": 1119284, "suburb": "Glen Forrest"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "An easy way to discover your parcel_number is by going to https://geohub-mundaring.hub.arcgis.com/, and use the Property Map to search for your address ensuring both Lot Numbers and House Number checkboxes are ticked. The pop-up that appears contains an entry that shows your parcel number."
    }
    COUNTRY = "au"
    PARAMS = (
        text_field("parcel_number", "Parcel number"),
        district("suburb"),
    )

    retrieve = calendar_retriever
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "FOGO Bin": wt.ORGANIC,
            "Recycle Bin": wt.RECYCLABLES,
            "General Waste": wt.GENERAL_WASTE,
            "Bulk Verge Collection": wt.BULKY_WASTE,
        },
    )
