from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _label(row) -> str:
    return row.find("td").get_text(strip=True)


def _next_date(row) -> str | None:
    """Only the "Next ... collection date" rows carry a date."""
    if not _label(row).startswith("Next"):
        return None
    return row.find_all("td")[1].get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Stafford Borough Council"
    DESCRIPTION = "Source for bin collection services for Stafford Borough Council, UK."
    URL = "https://www.staffordbc.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "domestic": {"uprn": "100031780029"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details."
        ),
    }

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: f"https://www.staffordbc.gov.uk/address/{uprn}",
    )
    parse = parsers.HtmlParser("table.my-area tr")
    transform = HtmlTransformer(
        date_getter=_next_date,
        type_getter=_label,
        parse_date=date_parsers.for_format("%a %d %b %Y"),
        type_value_map={
            "Next refuse (green bin) collection date": wt.GENERAL_WASTE,
            "Next recycling (blue bin and bag) collection date": wt.RECYCLABLES,
        },
    )
