"""City of Karlsruhe (karlsruhe.de).

Composes: :class:`~waste_collection_schedule.retrievers.FirstMatchRetriever`.
The city publishes the same ICS export on two load-balanced hosts
(``web4``/``web6``) under a per-year path, and which combination is live is
only discoverable by asking, so the source POSTs each of the six in turn
(current, next, previous year x both hosts) and keeps the first that comes back
with events. That candidate-fallback shape is now a shared retriever rather
than a source-local loop; everything else (``IcsParser`` + ``ICSTransformer``)
is standard.

The legacy comment recorded a ``SSLCertVerificationError`` with
``verify=True`` and worked around it with ``verify=False``. Re-checked live
during the pipeline conversion: both curl_cffi (browser impersonation) and
plain ``requests`` reach every host/year combination with default TLS
verification now, so ``verify=False`` is not carried forward — the provider's
certificate has apparently since been fixed.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://web{i}.karlsruhe.de/service/abfall/akal/akal_{year}.php"


def _clean_first_segment(label: str) -> str:
    """Keep only the text before the first comma (legacy behaviour)."""
    return label.split(",")[0].strip()


def _years_by_host(**_) -> list[tuple[int, int]]:
    """Every (year, host) combination worth asking, most likely first."""
    now = datetime.now()
    return [
        (year, host)
        for year in (now.year, now.year + 1, now.year - 1)
        for host in (4, 6)
    ]


def _has_events(response) -> bool:
    """True once a candidate answers with a populated calendar.

    An unserved year or a host that has not been given the file answers 200
    with an empty calendar rather than an error, so the status code cannot tell
    the candidates apart.
    """
    return "BEGIN:VEVENT" in response.text


@final
class Source(BaseSource):
    TITLE = "City of Karlsruhe"
    DESCRIPTION = "Source for City of Karlsruhe."
    URL = "https://www.karlsruhe.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Östliche Rheinbrückenstraße 1": {
            "street": "Östliche Rheinbrückenstraße",
            "hnr": 1,
        },
        "Habichtweg 4": {"street": "Habichtweg", "hnr": 4},
        "Machstraße 5": {"street": "Machstraße", "hnr": 5},
        "Bernsteinstraße 10 ladeort 1": {
            "street": "Bernsteinstraße",
            "hnr": 10,
            "ladeort": 1,
        },
        "Bernsteinstraße 10 ladeort 2": {
            "street": "Bernsteinstraße",
            "hnr": 10,
            "ladeort": 2,
        },
    }

    PARAMS = (
        street("street"),
        house_number("hnr"),
        text_field("ladeort", label="Ladeort", optional=True),
    )

    retrieve = retrievers.FirstMatchRetriever(
        candidates=_years_by_host,
        url=lambda candidate, **_: _API_URL.format(year=candidate[0], i=candidate[1]),
        method="POST",
        data=lambda candidate, street, hnr, ladeort=None, **_: {
            "strasse_n": street,
            "hausnr": hnr,
            "ical": "+iCalendar",
            "ladeort": ladeort,
        },
        params=lambda candidate, hnr, **_: {"hausnr": hnr},
        accept=_has_events,
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Bioabfall": ORGANIC,
            "Papier": PAPER,
            "Wertstoff": RECYCLABLES,
            "Sperrmüllabholung": BULKY_WASTE,
        },
        clean=_clean_first_segment,
    )

    def __init__(self, street: str, hnr: str | int, ladeort: int | None = None):
        super().__init__(street=street, hnr=hnr, ladeort=ladeort)
