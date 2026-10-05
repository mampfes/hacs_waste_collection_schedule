import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, street, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

_BASE_URL = "https://www.slough.gov.uk"
_SEARCH_URL = f"{_BASE_URL}/directory/search"
_RECORD_URL = f"{_BASE_URL}/directory-record"

# The bins the directory record page lists a schedule page for.
_BIN_KEYWORDS = ("grey bin", "red bin", "green bin", "food waste")

_RECORD_HREF = re.compile(r"/directory-record/(\d+)/")
_SCHEDULE_HREF = re.compile(r"/bin-collections/")


def _record_id(*_keys, record_id=None, **_) -> str | None:
    """A directory record id the user supplied, which skips the street search."""
    return record_id


def _pick_record(response, *_keys, street=None, **_) -> str:
    """The directory record id for the street name, from the search results."""
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for a in soup.select("ul.list--record li.list__item a.list__link"):
        match = _RECORD_HREF.match(a.get("href", ""))
        if match:
            results.append((match.group(1), a.get_text(strip=True)))
    if not results:
        raise SourceArgumentNotFound("street", street)
    if len(results) == 1:
        return results[0][0]
    exact = [rid for rid, name in results if name.lower() == street.lower()]
    if len(exact) == 1:
        return exact[0]
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, [name for _, name in results]
    )


def _schedule_urls(response, *keys, **_) -> list[str]:
    """The schedule page of each bin listed on a directory record page."""
    record_id = keys[-1]
    soup = BeautifulSoup(response.text, "html.parser")
    definitions = soup.find("dl")
    if not definitions:
        raise SourceArgumentNotFound("record_id", record_id)
    urls = []
    for heading in definitions.find_all("dt"):
        text = heading.get_text(strip=True).lower()
        if not any(keyword in text for keyword in _BIN_KEYWORDS):
            continue
        content = heading.find_next_sibling("dd")
        link = content.find("a", href=_SCHEDULE_HREF) if content else None
        if link:
            href = link["href"]
            urls.append(href if href.startswith("http") else _BASE_URL + href)
    if not urls:
        raise SourceArgumentNotFound("record_id", record_id)
    return urls


def _bin_name(title: str) -> str:
    """ "Grey bin Thursday week A collection dates" -> "Grey bin"."""
    return " ".join(title.split()[:2])


@final
class Source(BaseSource):
    TITLE = "Slough Borough Council"
    DESCRIPTION = "Source for slough.gov.uk services for Slough Borough Council."
    URL = "https://www.slough.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Knolton Way, Montgomery Place": {
            "record_id": 34771,
        },
        "Abbey Close (wheelie bins)": {
            "record_id": 34035,
        },
        "Anslow Place (communal bins)": {
            "record_id": 34069,
        },
        "Search by street name": {
            "street": "Knolton Way, Montgomery Place",
        },
    }

    PARAMS = (
        alternatives(
            [text_field("record_id", label="Directory record ID")],
            [street("street")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your street at https://www.slough.gov.uk/bin-collections "
            "and note the number from the URL of your matching result (for "
            "example 34771 from /directory-record/34771/...). Use that number as "
            "the directory record ID, or give the exact street name as listed in "
            "the directory instead (for example 'Knolton Way, Montgomery Place'). "
            "Use one of the two, not both."
        ),
    }

    # The directory record page links one schedule page per bin; each lists that
    # bin's collection dates, and is titled with the bin ("Grey bin Thursday
    # week A collection dates").
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(
                _SEARCH_URL,
                params=lambda street=None, **_: {
                    "directoryID": "30",
                    "keywords": street,
                    "submit": "Search",
                },
                given=_record_id,
                pick=_pick_record,
            ),
            retrievers.Lookup(
                lambda found_id, **_: f"{_RECORD_URL}/{found_id}/bin-day",
                pick=_schedule_urls,
            ),
        ),
        targets=lambda source, keys: keys[-1],
        fetch=retrievers.Request(lambda url, keys, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.HtmlLabelledDates(
            "div.site-content__flex-wrapper",
            label="h1",
            date=":scope",
            # Not the bounds of a "No collections from 22 December 2025 to
            # 4 January 2026" notice, which is listed beside the real dates.
            date_pattern=r"(?<!from )(?<!to )(?<!\d)(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            all_dates=True,
            parse_date=date_parsers.for_format("%d %B %Y"),
        )
    )
    transform = RowTransformer(
        clean=_bin_name,
        type_value_map={
            "Grey bin": wt.GENERAL_WASTE,
            "Red bin": wt.RECYCLABLES,
            "Green bin": wt.GARDEN_WASTE,
        },
    )
