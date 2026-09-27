import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer


def _payload(uprn, **_) -> dict:
    return {
        "getCollectionByUprnAndDate": {
            "getCollectionByUprnAndDateInput": {
                # The council's UPRNs are twelve digits, zero-padded.
                "uprn": str(uprn).zfill(12),
                "nextCollectionFromDate": datetime.date.today().strftime("%Y/%m/%d"),
            }
        }
    }


@final
class Source(BaseSource):
    TITLE = "London Borough of Havering"
    DESCRIPTION = "Source for London Borough of Havering."
    URL = "https://www.havering.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "53 Argyle Gardens": {"uprn": "100021403735"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url="https://api-prd.havering.gov.uk/whitespace/GetCollectionByUprnAndDate",
        json=_payload,
        # The council's public site key for its own API gateway.
        headers={
            "Ocp-Apim-Trace": "true",
            "Ocp-Apim-Subscription-Key": "545bcf53c9094dfd980dd9da72b0514d",
        },
    )
    parse = parsers.JsonParser(
        "getCollectionByUprnAndDateResponse",
        "getCollectionByUprnAndDateResult",
        "Collections",
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="service",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        type_value_map={
            "Service - Domestic Waste": wt.GENERAL_WASTE,
            "Service - Garden Waste": wt.GARDEN_WASTE,
            "Service - Garden Waste Winter": wt.GARDEN_WASTE,
            "Service - Recycling": wt.RECYCLABLES,
        },
    )
