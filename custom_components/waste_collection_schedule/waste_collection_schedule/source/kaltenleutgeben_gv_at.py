from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.transformers import HtmlTransformer

OVERVIEW_URL = "https://www.kaltenleutgeben.gv.at/Muellkalender_NEU"


def _detail_urls(response, *keys, **_) -> list[str]:
    """Every row of the overview table links to the detail page of one waste type."""
    soup = BeautifulSoup(response.text, "html.parser")
    return [
        urljoin(OVERVIEW_URL, anchor["href"])
        for anchor in soup.select("table.ris_table tr a[href]")
    ]


def _type(item) -> str:
    """The heading of the detail page the date belongs to."""
    return item.find_parent("form").select_one("h1").get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Kaltenleutgeben"
    DESCRIPTION = (
        "Waste collection schedule for Marktgemeinde Kaltenleutgeben, Austria."
    )
    URL = "https://www.kaltenleutgeben.gv.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC]

    # The waste calendar publishes a single town-wide schedule, so no address
    # is required.
    TEST_CASES: ClassVar[dict] = {"Kaltenleutgeben": {}}

    PARAMS = ()

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(OVERVIEW_URL, pick=_detail_urls),
        targets=lambda source, urls: urls,
    )

    parse = parsers.EachResponse(
        parsers.HtmlParser("span.ris_kal_dateitem", require=["h1"])
    )

    transform = HtmlTransformer(
        date_getter=lambda item: item.get_text(strip=True).split(",")[-1].strip(),
        type_getter=_type,
        type_value_map={
            "Restmüll 770l und 1.100l Gefäße": wt.GENERAL_WASTE,
            "Restmüll 80l und 120 l Gefäße": wt.GENERAL_WASTE,
            "Biomüll": wt.ORGANIC,
        },
        parse_date=date_parsers.for_format("%d.%m.%Y"),
    )
