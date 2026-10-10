import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field, uprn
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer, label_cleaner


@final
class Source(BaseSource):
    TITLE = "Windsor and Maidenhead"
    DESCRIPTION = "Source for Windsor and Maidenhead."
    URL = "https://my.rbwm.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Windsor 1": {"postcode": "SL4 4EN", "uprn": 100080381393},
        "Windsor 2": {"postcode": "", "uprn": "100080384194"},
        "Maidenhead 1": {"uprn": "100080359672"},
        "Maidenhead 2": {"uprn": 100080355442},
    }

    # The postcode is not used; it stays optional so existing configurations
    # keep working.
    PARAMS = (uprn(), text_field("postcode", term=POSTCODE, optional=True))

    retrieve = HttpGetRetriever(
        url="https://forms.rbwm.gov.uk/bincollections",
        # The council's UPRNs are twelve digits, zero-padded.
        params=lambda uprn, **_: {"uprn": str(uprn).zfill(12)},
    )
    parse = parsers.HtmlParser("table tr:has(> td:nth-of-type(2))")
    # "29th September 2026"
    transform = HtmlTransformer(
        date_getter=lambda row: re.sub(
            r"(\d)(st|nd|rd|th)", r"\1", row.select("td")[1].get_text(strip=True)
        ),
        type_getter=lambda row: row.select("td")[0].get_text(strip=True),
        parse_date=date_parsers.for_format("%d %B %Y"),
        clean=label_cleaner(strip_suffixes=[" Collection Service"]),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Food Waste": wt.FOOD_WASTE,
        },
    )
