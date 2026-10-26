import re
import unicodedata
from collections.abc import Sequence
from typing import ClassVar, final
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city
from waste_collection_schedule.retrievers import (
    FanOutRetriever,
    HttpGetRetriever,
    Request,
)
from waste_collection_schedule.service.NkomLt import NkomParser
from waste_collection_schedule.transformers import JsonTransformer

TITLE = "Nemėžio komunalininkas"
DESCRIPTION = "Waste collection schedules for Vilnius District, Lithuania."
URL = "https://www.nkom.lt/kita.html"
PAGE_URL = URL
COUNTRY = "lt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}


def _fold(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value).casefold()
        if not unicodedata.combining(character)
    )


def _schedule_kind(href: str) -> str | None:
    filename = _fold(unquote(urlparse(href).path))
    if not filename.endswith(".pdf") or "grafikas" not in filename:
        return None
    if "pakuociu" in filename:
        return "packaging"
    if "misriu" in filename:
        return "mixed"
    return None


def _schedule_period(href: str) -> tuple[int, int]:
    match = re.search(r"\b(20\d{2})\b.*?\((\d{1,2})-(\d{1,2})\)", unquote(href))
    if match is None:
        return (0, 0)
    return (int(match.group(1)), int(match.group(3)))


def _schedule_targets(_source, response) -> Sequence[tuple[str, str]]:
    schedules: dict[str, tuple[tuple[int, int], str]] = {}
    soup = BeautifulSoup(response.text, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = urljoin(PAGE_URL, str(anchor["href"]))
        kind = _schedule_kind(href)
        if kind is None:
            continue
        period = _schedule_period(href)
        if kind not in schedules or period > schedules[kind][0]:
            schedules[kind] = (period, href)

    missing = {"mixed", "packaging"} - schedules.keys()
    if missing:
        raise ValueError(
            f"Could not find current NKOM PDF schedule(s): {', '.join(sorted(missing))}"
        )
    return [(kind, schedule[1]) for kind, schedule in sorted(schedules.items())]


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY
    TEST_CASES: ClassVar[dict] = {
        "Nemėžio grafikai": {"location": "Nemėžis"},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Open https://www.nkom.lt/kita.html and use a town, village, or street name as it appears in the 'Vietovė' column of the schedule."
    }
    PARAMS = (city("location"),)
    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
    ]
    RAISE_ON_EMPTY = True

    retrieve = FanOutRetriever(
        prepare=HttpGetRetriever(url=PAGE_URL, headers=HEADERS),
        targets=_schedule_targets,
        fetch=Request(url=lambda target, _page, **_: target[1], headers=HEADERS),
    )
    parse = parsers.EachResponse(NkomParser())
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "mixed": wt.GENERAL_WASTE,
            "packaging": wt.RECYCLABLES,
            "glass": wt.GLASS,
        },
    )
