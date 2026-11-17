import re
from typing import ClassVar, final
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://m.wetzikon.ch"
# The "Entsorgungskalender" page. It links one page per Kreis, and each Kreis
# page links one page per waste type. Every waste type page publishes its dates
# as an ICS feed keyed by the page's own apid.
CALENDAR_HOME_ID = "7215088"
CALENDAR_HOME_URL = f"{BASE_URL}/index.php?apid={CALENDAR_HOME_ID}"
ICAL_URL = f"{BASE_URL}/appl/ical.php"


def _links(response) -> dict[str, str]:
    """``{link title: absolute url}`` for the list entries of a calendar page."""
    soup = BeautifulSoup(response.text, "html.parser")
    links: dict[str, str] = {}
    for anchor in soup.select("div.elementLinkRow a[href]"):
        title = anchor.select_one("div.title")
        if title is not None:
            links[title.get_text(strip=True)] = urljoin(
                str(response.url), str(anchor["href"])
            )
    return links


def _query(url: str, key: str) -> str | None:
    values = parse_qs(urlparse(url).query).get(key)
    return values[0] if values else None


def _kreis_url(response, *_keys, district, **_) -> str:
    """The calendar page of the configured Kreis."""
    kreise = {
        match.group(1): url
        for title, url in _links(response).items()
        if (match := re.fullmatch(r"Kreis (\d+)", title))
    }
    number = "".join(re.findall(r"\d", str(district)))
    if number not in kreise:
        raise SourceArgumentNotFoundWithSuggestions(
            "district", district, sorted(kreise, key=int)
        )
    return kreise[number]


def _feed_ids(response, kreis_url, **_) -> list[str]:
    """The apids of the Kreis page's waste type pages (one ICS feed each).

    Only children of the Kreis page are calendars; anything else linked from it
    (a collection point, say) is skipped.
    """
    kreis_id = _query(kreis_url, "apid")
    return [
        apid
        for url in _links(response).values()
        if _query(url, "apparentid") == kreis_id and (apid := _query(url, "apid"))
    ]


@final
class Source(BaseSource):
    TITLE = "Wetzikon ZH"
    DESCRIPTION = "Source for waste collection in Wetzikon ZH, Switzerland."
    URL = "https://www.wetzikon.ch/"
    COUNTRY = "ch"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@danielLutziger"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Kreis 1": {"district": "1"},
        "Kreis 2": {"district": "2"},
        "Kreis 3": {"district": "3"},
        "Kreis 4": {"district": "4"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown Kreis": {"district": "9"},
    }

    PARAMS = (district(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the number of your collection district (Kreis 1, 2, 3 or 4). "
            "Each Kreis page at https://m.wetzikon.ch/index.php?apid=7215088 "
            "lists its streets."
        ),
        "de": (
            "Geben Sie die Nummer Ihres Entsorgungskreises ein (Kreis 1, 2, 3 "
            "oder 4). Die Strassen jedes Kreises finden Sie unter "
            "https://m.wetzikon.ch/index.php?apid=7215088."
        ),
        "fr": (
            "Saisissez le numéro de votre secteur de collecte (Kreis 1, 2, 3 ou "
            "4). Les rues de chaque secteur figurent sur "
            "https://m.wetzikon.ch/index.php?apid=7215088."
        ),
        "it": (
            "Inserite il numero del vostro circolo di raccolta (Kreis 1, 2, 3 o "
            "4). Le strade di ogni circolo sono elencate su "
            "https://m.wetzikon.ch/index.php?apid=7215088."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
        wt.OTHER,
    ]

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(CALENDAR_HOME_URL, pick=_kreis_url),
            retrievers.Lookup(lambda kreis_url, **_: kreis_url, pick=_feed_ids),
        ),
        targets=lambda source, context: context[1],
        fetch=retrievers.Request(
            ICAL_URL,
            params=lambda feed_id, context, **_: {
                "apid": feed_id,
                "calhome": CALENDAR_HOME_ID,
            },
        ),
    )
    # A Kreis-specific round is titled "Kreis 2, Abfall"; a city-wide one just
    # "Papiersammlung". A seasonal round's feed may be empty, so no min_events.
    parse = parsers.EachResponse(parsers.IcsParser(regex=r"^(?:Kreis \d+, )?(.+)$"))
    transform = ICSTransformer(
        type_value_map={
            "Abfall": wt.GENERAL_WASTE,
            "Biogene Abfälle": wt.ORGANIC,
            # Cardboard and paper are collected in separate rounds.
            "Karton": wt.PAPER,
            "Papiersammlung": wt.PAPER,
            # Chipping of shrub and tree cuttings, on request.
            "Häckseldienst": wt.GARDEN_WASTE,
            # Inert waste: glass panes, mirrors, stones, concrete, crockery.
            "Grubengut": wt.OTHER,
            # Scrap metal round, not packaging metal (wt.METAL).
            "Metall": wt.OTHER,
        },
        carry_raw_label=True,
    )
