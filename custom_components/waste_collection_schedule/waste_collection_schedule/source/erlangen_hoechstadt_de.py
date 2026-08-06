"""Landkreis Erlangen-Höchstadt.

Demonstrates: the "year-window, single feed per year" shape, which turned out to
need no source code at all. The provider's ICS endpoint takes the year as a
query parameter, and ``IcsSessionRetriever`` already fetches one feed per
calendar year the schedule can span: the current year and, in December, the
following one too, since the provider publishes it early. There are no
preparatory requests to make here, so ``steps`` stays empty and the retriever
reduces to that per-year GET, with ``IcsFeedsParser`` merging the years.

``require_lookahead=True`` keeps the year-end contract the hand-written
``retrieve`` had: a provider that answers for the current year but errors on the
following one is a provider that has changed something, and is worth surfacing
rather than half-swallowing. An *empty* following year is a different thing and
still passes through, leaving the current year's collections intact.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.erlangen-hoechstadt.de/komx/surface/dfxabfallics/GetAbfallIcs"


def _feed_params(year: int, city: str, street: str, **_: object) -> "dict[str, object]":
    return {
        "ort": city.upper(),
        "strasse": street,
        "abfallart": "Alle",
        "jahr": year,
    }


@final
class Source(BaseSource):
    TITLE = "Landkreis Erlangen-Höchstadt"
    DESCRIPTION = "Source for Landkreis Erlangen-Höchstadt"
    URL = "https://www.erlangen-hoechstadt.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Höchstadt": {"city": "Höchstadt", "street": "Böhmerwaldstraße"},
        "Brand": {"city": "Eckental", "street": "Eckenhaid, Amselweg"},
        "Ortsteile": {"city": "Wachenroth", "street": "Ort inkl. aller Ortsteile"},
    }

    PARAMS = (city(), street())

    retrieve = IcsSessionRetriever(
        feed_url=_API_URL,
        feed_params=_feed_params,
        encoding="utf-8",
        require_lookahead=True,
    )

    parse = IcsFeedsParser(parsers.IcsParser(split_at=" / "))

    # No WASTE_TYPES. A bare pass-through transformer has no
    # type_value_map, so every label this feed sends is classified by the
    # shared multilingual vocabulary, which cannot be enumerated
    # statically; and with no cassette yet (#7051) the produced set
    # cannot be derived by replay either. An empty declaration is the
    # honest one, and it only narrows a config-flow dropdown offer
    # (#7028). Declare the real vocabulary once this source is recorded.
    transform = ICSTransformer()
