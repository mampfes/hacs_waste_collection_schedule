from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.parsers import ArgumentGuard, JsonParser
from waste_collection_schedule.preprocessors import Compose, ExplodeList, RowFilter
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer, label_cleaner


@final
class Source(BaseSource):
    TITLE = "Winnipeg (MB)"
    DESCRIPTION = "Source script for https://myutility.winnipeg.ca Use the same address as that works on the website under 'Find your collection day'"
    URL = "https://myutility.winnipeg.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestWinnipeg": {"address": "123 EASY ST"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use the same address that works on https://myutility.winnipeg.ca "
            "under 'Find your collection day'."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://myutility.winnipeg.ca/UtilityBillingService/CollectionManagement/getCollectionManagementDetails",
        params=lambda address, **_: {"address": address.upper()},
    )

    # An unknown address is answered with a small object without "Address".
    parse = ArgumentGuard(
        JsonParser("Address"),
        argument="address",
        contains='"Address":{',
        hint="use the address that works under 'Find your collection day' on the website",
    )

    # One record per waste type of each pickup day, for the types this address
    # is eligible for (public holidays are listed with IsEligible false).
    preprocess = Compose(
        ExplodeList("PickUpDateDetails"),
        ExplodeList("WasteTypes", into="waste"),
        RowFilter(lambda record, source: record["waste"]["IsEligible"]),
    )

    transform = JsonTransformer(
        date_key="Date",
        type_key=lambda record: record["waste"]["WasteType"],
        # "Yard Waste - A" is the A-week variant of "Yard Waste"
        clean=label_cleaner(strip_suffixes=[" - A"]),
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Yard Waste": wt.GARDEN_WASTE,
            # eligible notices that are not collections
            "Giveaway weekend": None,
            "Waste reduction week": None,
        },
    )
