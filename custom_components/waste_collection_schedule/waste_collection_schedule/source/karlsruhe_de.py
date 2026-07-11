"""City of Karlsruhe (karlsruhe.de).

Demonstrates: an ICS POST that needs a custom ``retrieve`` override rather
than a shared retriever — the legacy source tries up to six URL variants
(current/next/previous year x two load-balanced hosts, ``web4``/``web6``)
until one returns a populated calendar. None of the shared retrievers model a
multi-host/multi-year fallback, so this stays a plain method override;
everything else (``IcsParser`` + ``ICSTransformer``) is standard.

The legacy comment recorded a ``SSLCertVerificationError`` with
``verify=True`` and worked around it with ``verify=False``. Re-checked live
during this conversion: both curl_cffi (browser impersonation) and plain
``requests`` reach every host/year combination with default TLS verification
now, so ``verify=False`` is dropped rather than carried forward — the
provider's certificate has apparently since been fixed.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers
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

    def retrieve(self, source: "Source"):
        """Try each year x host combination until one returns real events.

        Mirrors the legacy ``fetch()``/``get_data()`` retry exactly: for each
        of (this year, next year, last year) x (host 4, host 6), POST and
        accept the first response containing at least one ``VEVENT``. If none
        do, return the last response received (so the parser's own shape
        check surfaces a clear error) or, failing even that, re-raise the
        last transport error.
        """
        now = datetime.now()
        data = {
            "strasse_n": source.params["street"],
            "hausnr": source.params["hnr"],
            "ical": "+iCalendar",
            "ladeort": source.params.get("ladeort"),
        }
        params = {"hausnr": source.params["hnr"]}

        last_response = None
        last_error: Exception | None = None
        for year in (now.year, now.year + 1, now.year - 1):
            for i in (4, 6):
                url = _API_URL.format(year=year, i=i)
                try:
                    response = source.session.post(
                        url,
                        data=data,
                        params=params,
                        timeout=30,
                    )
                except Exception as e:
                    last_error = e
                    continue
                last_response = response
                if "BEGIN:VEVENT" in response.text:
                    return response
        if last_response is not None:
            return last_response
        raise last_error  # type: ignore[misc]
