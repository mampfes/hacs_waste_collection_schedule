from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import RowTransformer

_API_URL = "https://cag.walsall.gov.uk/BinCollections/GetBins"


def _schedule_urls(response, *_, uprn=None, **__) -> list[str]:
    """Lookup pick: the per-bin schedule page links of the property."""
    soup = BeautifulSoup(response.text, "html.parser")
    urls = [
        urljoin(_API_URL, str(a["href"]))
        for a in soup.select("a.select-bin[href]")
        if "roundname" in str(a["href"])
    ]
    if not urls:
        raise SourceArgumentNotFound("uprn", uprn)
    return urls


@final
class Source(BaseSource):
    TITLE = "Walsall Council"
    DESCRIPTION = "Source for waste collection services from Walsall Council"
    URL = "https://www.walsall.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "test001": {"uprn": "100071103746"},
        "test002": {"uprn": 100071105627},
        "test003": {"uprn": "100071095946"},
        "test004": {"uprn": 100071048794},
    }

    PARAMS = (uprn(),)

    # The property page links one schedule page per bin; each page names its
    # bin in the heading and lists the dates in a table.
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _API_URL,
            params=lambda uprn, **_: {"uprn": uprn},
            pick=_schedule_urls,
        ),
        targets=lambda source, urls: urls,
    )

    parse = parsers.EachResponse(
        parsers.HtmlLabelledDates(
            "div.col-md-8",
            label="h1",
            date=":scope",
            date_pattern=r"(\d{2}/\d{2}/\d{4})",
            all_dates=True,
        )
    )

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Bin collection schedule for grey bin (general waste)": wt.GENERAL_WASTE,
            "Bin collection schedule for green bin (recycling)": wt.RECYCLABLES,
            "Bin collection schedule for brown bin (garden waste)": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
