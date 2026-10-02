from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://www.calderdale.gov.uk/environment/waste/household-collections/collectiondayfinder.jsp"


def _label(row) -> str:
    """The bin's name, in bold in the first cell."""
    return row.find("td").find("strong").get_text(strip=True)


def _next_date(row) -> str | None:
    """ "Friday 9 October 2026 will be your next collection." in the third cell."""
    for paragraph in row.find_all("td")[2].find_all("p"):
        if "will be your next collection" in paragraph.get_text():
            return paragraph.find("strong").get_text(strip=True)
    return None


@final
class Source(BaseSource):
    TITLE = "Calderdale Council"
    DESCRIPTION = "Source for calderdale.gov.uk services for Calderdale Council, UK."
    URL = "https://www.calderdale.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Test_1": {"postcode": "OL14 7BX", "uprn": "010010152783"},
        "Test_2": {"postcode": "HX1 3UZ", "uprn": "010006741170"},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details. Leading zeros may be left out."
        ),
    }

    retrieve = HttpPostRetriever(
        API_URL,
        data=lambda postcode, uprn, **_: {
            "postcode": postcode,
            "uprn": str(uprn).zfill(12),
            "gdprTerms": "Yes",
            "privacynoticeid": "323",
            "find": "Show me my collection days",
        },
    )

    # The finder answers an unknown UPRN with a page that does not name the address.
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser("table#collection tr"),
        argument="uprn",
        contains="Currently showing collection days for:",
        hint=(
            "check that the postcode and UPRN match, and that "
            "calderdale.gov.uk's collection day finder is available"
        ),
    )

    transform = HtmlTransformer(
        date_getter=_next_date,
        type_getter=_label,
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "Recycling": wt.RECYCLABLES,
            "Waste": wt.GENERAL_WASTE,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
