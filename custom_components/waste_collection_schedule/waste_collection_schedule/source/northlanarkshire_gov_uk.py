from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field, uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "North Lanarkshire Council"
    DESCRIPTION = "Source for waste collection services for North Lanarkshire Council"
    URL = "https://northlanarkshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "118026605", "usrn": "48406574"},
        "Test_002": {"uprn": 118177268, "usrn": 48410258},
        "Test_003": {"uprn": "000118035256", "usrn": "48409125"},
    }

    PARAMS = (uprn(), text_field("usrn", "USRN (Unique Street Reference Number)"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Look your address up on the council's bin collection dates page; its "
            "URL has the form www.northlanarkshire.gov.uk/bin-collection-dates/UPRN/USRN."
        ),
    }

    retrieve = HttpGetRetriever(
        # The council's UPRNs are twelve digits, zero-padded.
        url=lambda uprn, usrn, **_: (
            "https://www.northlanarkshire.gov.uk/bin-collection-dates/"
            f"{str(uprn).zfill(12)}/{usrn}"
        ),
    )
    # One box per bin: its name, its weekday, then its dates.
    parse = parsers.HtmlLabelledDates(
        "div.waste-type-container",
        label="h3",
        date=":scope",
        date_pattern=r"\d{2} \w+ \d{4}",
        parse_date=date_parsers.for_format("%d %B %Y"),
        all_dates=True,
    )
    transform = RowTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Blue-lidded Recycling Bin": wt.RECYCLABLES,
            "Food and Garden": wt.ORGANIC,
            "Paper and Card": wt.PAPER,
            "Glass, Metals, Plastics and Cartons": wt.RECYCLABLES,
            "Glass": wt.GLASS,
        },
    )
