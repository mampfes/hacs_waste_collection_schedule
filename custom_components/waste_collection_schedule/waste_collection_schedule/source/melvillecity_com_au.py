from typing import ClassVar, final

from dateutil.parser import parse as _dateutil_parse
from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.IntraMaps import (
    IntegrationClientConfig,
    IntegrationClientRetriever,
    IntegrationPanelParser,
    nominatim_reproject,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# The only Integration API council of the three that needs a geocode step
# first: its single search form takes reprojected map coordinates rather than
# a free-text address, and returns the collection fields directly (no
# separate mapkey/dbkey details form). GreenLid (FOGO) is a weekly collection
# whose weekday lives in a SEPARATE "collection_district" field, so it can't
# be read from one column alone the way RecurrenceExpander's per-record
# describe() assumes; preprocess is overridden as a method instead, reading
# the whole field set at once. RedLid/YellowLid each carry their own explicit
# next-collection date (fortnightly).

INTRAMAPS_CONFIG = IntegrationClientConfig(
    base_url="https://melville.spatial.t1cloud.com",
    instance="spatial/intramaps",
    api_key="bb6fcd4c-7de3-4ce5-8f6d-dc3335ffb26e",
    config_id="3f105b05-d2ee-419c-8265-1ab592559a33",
    project="78ad3422-3dd6-4540-b318-782d4d1313a0",
)

WASTE_FORM_ID = "0e72c05c-0181-428a-b4e0-e2be69cf69dc"

_TYPE_MAP = {
    "FOGO": ORGANIC,
    "General Waste": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
}


@final
class Source(BaseSource):
    TITLE = "City of Melville"
    DESCRIPTION = "Source for City of Melville waste collection."
    URL = "https://www.melvillecity.com.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Williams Road": {"address": "43 Williams Road, Melville, WA"},
        "Canning Highway": {"address": "356 Canning Highway, Bicton, WA"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '43 Williams Road, Melville, WA'). "
            "Search at https://www.melvillecity.com.au/waste-and-environment/"
            "waste-recycling-fogo/residential-bins"
        ),
    }

    retrieve = IntegrationClientRetriever(
        INTRAMAPS_CONFIG,
        search_form=WASTE_FORM_ID,
        geocode=nominatim_reproject(
            "address", epsg_out="epsg:7850", country_codes="au"
        ),
    )
    parse = IntegrationPanelParser()

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)

    def preprocess(self, records, source=None):
        """Combine GreenLid's presence with its weekday from a sibling field.

        The one place in this source that needs more than a single column:
        GreenLid's own value only signals "this address has a FOGO service",
        the weekday it runs on is a separate "collection_district" field.
        """
        fields = {r.get("column", ""): r.get("value", "") for r in records}

        if fields.get("GreenLid"):
            weekday = recurrence.weekday(fields.get("collection_district", ""))
            if weekday is not None:
                start = recurrence.next_weekday(weekday)
                for collection_date in recurrence.recurring(
                    start, recurrence.WEEKLY, 26
                ):
                    yield collection_date, "FOGO"

        for column, key in (("RedLid", "General Waste"), ("YellowLid", "Recycling")):
            text = fields.get(column, "").strip()
            if not text:
                continue
            try:
                # dayfirst=True: the provider's next-collection date is
                # day/month/year, which dateutil's default US-style guess
                # would otherwise misread.
                start = _dateutil_parse(text, dayfirst=True).date()
            except (ValueError, TypeError):
                continue
            for collection_date in recurrence.recurring(
                start, recurrence.FORTNIGHTLY, 13
            ):
                yield collection_date, key
