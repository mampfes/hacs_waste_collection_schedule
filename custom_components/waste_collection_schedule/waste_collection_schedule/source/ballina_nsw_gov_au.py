from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Ballina Shire Council"
    DESCRIPTION = "Source for Ballina Shire Council, NSW, Australia."
    URL = "https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "1/49 Grant Street BALLINA": {"address": "1/49 Grant Street BALLINA"},
        "2/7 Hartigan St CUMBALUM": {"address": "2/7 Hartigan St CUMBALUM"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter the full service address used by Ballina Shire Council, for "
        "example '1 Grant St, Ballina NSW 2478'."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.ballina.nsw.gov.au",
        # Ballina's fuzzy search ranks poorly: "1 Grant St, Ballina NSW 2478"
        # comes back with "2/7 Hartigan St CUMBALUM" first and the Grant Street
        # properties behind it. So the first hit cannot be trusted, and the
        # whole list is disambiguated against the address instead.
        search_fuzzy=True,
        page_link="/$8a878053-5e29-431d-896b-8c79ce08799f$/Residents/Waste-and-Recycling/Bin-Collection-Day",
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": "https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day",
            "x-requested-with": "XMLHttpRequest",
        },
        strict_address_matching=True,
        strict_single_result=True,
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "Landfill Bin Collection": wt.GENERAL_WASTE,
            "Recycling Bin Collection": wt.RECYCLABLES,
            "Food Organics Garden Organics Bin Collection": wt.ORGANIC,
        },
    )
