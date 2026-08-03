from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
)
from waste_collection_schedule.preprocessors import HtmlGroupedDates
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: HTML scraping where the waste type is encoded in the *container's*
# CSS class, not in each dated <li>. parsers.HtmlParser selects the per-type
# containers and preprocessors.HtmlGroupedDates reads the class to find the type
# and the <li> dates beneath it, yielding (date, class-token) rows for a plain
# ICSTransformer. The provider (c-trace) carries an ASP.NET session id in the URL
# path; the stale embedded token simply 302-redirects to a fresh one, which the
# shared session follows, so no separate token-priming request is needed.

# c-trace embeds a session id in the path; a stale value is refreshed by a 302.
_SESSION = "(S(y0ommq52pdbwa0jek4oqqzgr))"
_BASE_URL = (
    f"https://web.c-trace.de/ekotom-abfallkalender/{_SESSION}/kalendarzodpadow/abc"
)

# The discriminating c-trace CSS class on each container -> canonical waste type.
TYPE_MAP = {
    "rest": wt.GENERAL_WASTE,
    "glas": wt.GLASS,
    "plastik": wt.RECYCLABLES,
    "bio": wt.ORGANIC,
    "papier": wt.PAPER,
    "sperr": wt.BULKY_WASTE,
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
        city(),
        street(),
        house_number(field="nr"),
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
    preprocess = HtmlGroupedDates(
        keys=TYPE_MAP,
        date_pattern=r"\d{2}\.\d{2}\.\d{4}",
        parse_date=date_parsers.for_format("%d.%m.%Y"),
    )
    transform = ICSTransformer(type_value_map=TYPE_MAP)
