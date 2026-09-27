from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field, uprn
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.service.LocalGovWasteCollection import (
    CollectionDaysParser,
    uprn_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Cumberland Council"
    DESCRIPTION = "Source for cumberland.gov.uk services for Cumberland Council, UK."
    URL = "https://cumberland.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "CA28 7QS", "uprn": "100110319463"},
        "Test_002": {"postcode": "CA28 8LG", "uprn": 100110320734},
        "Test_003": {"postcode": "CA28 6SW", "uprn": "10000895390"},
        "Test_004": {"uprn": 10000895390},
    }

    # The postcode is no longer needed; it stays optional so existing
    # configurations keep working.
    PARAMS = (uprn(), text_field("postcode", term=POSTCODE, optional=True))

    retrieve = uprn_retriever(
        "https://www.cumberland.gov.uk/bins-recycling-and-street-cleaning/"
        "waste-collections/bin-collection-schedule"
    )
    parse = CollectionDaysParser()
    transform = RowTransformer(
        type_value_map={
            "Domestic Waste": wt.GENERAL_WASTE,
            "Glass, cans, tins, plastics and Tetra Paks": wt.RECYCLABLES,
            "Paper and card": wt.PAPER,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
