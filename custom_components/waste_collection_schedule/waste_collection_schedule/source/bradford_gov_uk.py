from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "General waste": wt.GENERAL_WASTE,
    "Recycling waste": wt.RECYCLABLES,
    "Garden waste": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Bradford Metropolitan District Council"
    DESCRIPTION = (
        "Source for Bradford.gov.uk services for Bradford Metropolitan Council, UK."
    )
    URL = "https://bradford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ilkley": {"uprn": "100051250665"},  # codespell:ignore ilkley
        "Bradford": {"uprn": "100051239296"},
        "Baildon": {"uprn": 10002329242},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    retrieve = retrievers.Request(
        "https://onlineforms.bradford.gov.uk/ufs/collectiondates.eb",
        cookies=lambda uprn, **_: {"COLLECTIONDATES": str(uprn)},
    )

    # One panel per service; its dates are the "Tue Oct 13 2026" lines, and an
    # unscheduled slot holds other text, which the pattern does not match.
    parse = parsers.HtmlLabelledDates(
        'table[role="region"][class*="Override-Panel"]',
        label='td[class*="Override-Header"]',
        date=":scope",
        date_pattern=r"([A-Z][a-z]{2} [A-Z][a-z]{2} \d{2} \d{4})",
        all_dates=True,
    )

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%a %b %d %Y"),
        type_value_map=_TYPE_MAP,
    )
