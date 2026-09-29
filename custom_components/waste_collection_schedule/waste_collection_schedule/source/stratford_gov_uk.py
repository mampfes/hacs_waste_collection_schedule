import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import HtmlTransformer

# The calendar is a grid: one row per date, one column per bin, and a tick image
# in each cell that is collected that day. Every ticked cell names its bin in its
# title ("Refuse (grey bin)"), so the ticked cells are the records.


@final
class Source(BaseSource):
    TITLE = "Stratford District Council"
    DESCRIPTION = (
        "Source for Stratford District Council and their 123+ bin collection system"
    )
    URL = "https://stratford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Stratford DC": {"uprn": "100071513500"},  # doesn't have food waste
        "Alscot Estate": {"uprn": 10024633309},
    }

    PARAMS = (uprn(),)

    # Only the UPRN matters, but the form needs the address keys to be present.
    retrieve = HttpPostRetriever(
        url="https://www.stratford.gov.uk/waste-recycling/when-we-collect.cfm/part/calendar",
        data=lambda uprn, **_: {
            "frmAddress1": "",
            "frmAddress2": "",
            "frmAddress3": "",
            "frmAddress4": "",
            "frmPostcode": "",
            "frmUPRN": str(uprn),
        },
    )
    parse = parsers.HtmlParser("table.table tbody td.text-center:has(img.check-img)")
    transform = HtmlTransformer(
        date_getter=lambda cell: cell.find_parent("tr").find("td").get_text(strip=True),
        type_getter=lambda cell: re.sub(r"\s*\(.*$", "", cell.get("title", "")),
        parse_date=date_parsers.for_format("%A, %d/%m/%Y"),
        type_value_map={
            "Food waste": wt.FOOD_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Refuse": wt.GENERAL_WASTE,
            "General refuse": wt.GENERAL_WASTE,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
