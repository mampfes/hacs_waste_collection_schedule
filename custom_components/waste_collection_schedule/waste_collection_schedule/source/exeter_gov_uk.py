from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://exeter.gov.uk/repositories/hidden-pages/address-finder/"


def _bin_heading(date: Tag) -> "str | None":
    """The <h2> naming the bin this <h3> date belongs to."""
    heading = date.find_previous_sibling("h2")
    return heading.get_text(strip=True) if isinstance(heading, Tag) else None


@final
class Source(BaseSource):
    TITLE = "Exeter City Council"
    DESCRIPTION = "Source for Exeter City services for Exeter City Council, UK."
    URL = "https://exeter.gov.uk/"
    COUNTRY = "uk"
    # An unknown UPRN answers an empty list rather than an error.
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@AtomBrake"]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100040227486"},
        "Test_002": {"uprn": "10013043921"},
        "Test_003": {"uprn": 10023120282},
        "Test_004": {"uprn": 100040241022},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown UPRN": {"uprn": "1"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Look up your address on the Exeter City Council 'When is my bin "
            "collected?' page; your UPRN is the number at the end of the "
            "resulting URL. Alternatively, search for your address on "
            "[Find My Address](https://www.findmyaddress.co.uk/)."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    # The council's firewall rejects a plain python-requests client; the
    # default curl_cffi session's Chrome fingerprint gets through.
    retrieve = HttpGetRetriever(
        url=API_URL,
        params=lambda uprn, **_: {"qsource": "UPRN", "qtype": "bins", "term": uprn},
    )
    # The reply is a one-element list whose "Results" field is HTML: each bin
    # is an <h2> followed by an <h3> holding its next date. A bin the property
    # doesn't have (garden waste without a subscription) has no <h3>, so
    # selecting the dates and reading back to their own heading never pairs a
    # date with the wrong bin.
    parse = parsers.HtmlParser("h3", require=["h2"], from_json_key=(0, "Results"))
    transform = HtmlTransformer(
        date_getter=lambda h3: h3.get_text(strip=True),
        type_getter=_bin_heading,
        type_value_map={
            "Refuse collection": wt.GENERAL_WASTE,
            "Recycling collection": wt.RECYCLABLES,
            "Garden waste collection": wt.GARDEN_WASTE,
            "Food waste collection": wt.FOOD_WASTE,
        },
    )
