import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Demonstrates: HTML scraping where the waste type is encoded in the *container's*
# CSS class, not in each dated <li>. parsers.HtmlParser selects the per-type
# containers; a method preprocess() reads the class to find the type and the <li>
# dates beneath it, yielding (date, class-token) rows for a plain ICSTransformer.
# The provider (c-trace) carries an ASP.NET session id in the URL path; the stale
# embedded token simply 302-redirects to a fresh one, which the shared session
# follows, so no separate token-priming request is needed.

# c-trace embeds a session id in the path; a stale value is refreshed by a 302.
_SESSION = "(S(y0ommq52pdbwa0jek4oqqzgr))"
_BASE_URL = (
    f"https://web.c-trace.de/ekotom-abfallkalender/{_SESSION}/kalendarzodpadow/abc"
)

_DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
_parse_date = date_parsers.for_format("%d.%m.%Y")

# The discriminating c-trace CSS class on each container -> canonical waste type.
TYPE_MAP = {
    "rest": GENERAL_WASTE,
    "glas": GLASS,
    "plastik": RECYCLABLES,
    "bio": ORGANIC,
    "papier": PAPER,
    "sperr": BULKY_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Czerwonak, Murowana Goślina, Oborniki"
    DESCRIPTION = (
        "Source for eko-tom.pl. Municipalities: Czerwonak, Murowana Goślina, Oborniki"
    )
    URL = "https://www.eko-tom.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    # The former "BIAŁĘŻYN / 1/A" case now returns "Brak harmonogramu" (no
    # schedule) upstream; dropped as stale. RAISE_ON_EMPTY surfaces such a dead
    # lookup as a clear argument error rather than the legacy silent empty list.
    TEST_CASES: ClassVar[dict] = {
        "Czerwonak": {"city": "Czerwonak", "street": "Źródlana", "nr": "39"},
    }

    PARAMS = (
        text_field("city", "City"),
        text_field("street", "Street"),
        text_field("nr", "House Number"),
    )

    retrieve = HttpGetRetriever(
        url=_BASE_URL,
        params=lambda city, street, nr, **_: {
            "Ort": city,
            "Strasse": street,
            "Hausnr": nr,
        },
    )
    parse = parsers.HtmlParser(".rest, .glas, .plastik, .bio, .papier, .sperr")
    transform = ICSTransformer(type_value_map=TYPE_MAP)

    def __init__(self, street: str, city: str, nr: str):
        super().__init__(city=city, street=street, nr=nr)

    def preprocess(
        self, containers: list[Tag], source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        for container in containers:
            classes = container.get("class") or []
            key = next((c for c in classes if c in TYPE_MAP), None)
            if key is None:
                continue
            for li in container.find_all("li"):
                match = _DATE_RE.search(li.get_text())
                if match:
                    yield _parse_date(match.group(0)), key
