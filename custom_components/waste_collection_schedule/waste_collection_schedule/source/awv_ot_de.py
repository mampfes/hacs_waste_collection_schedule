"""AWV: Abfall Wirtschaftszweckverband Ostthüringen.

Demonstrates: the "year-window, stateful POST-then-GET" shape, which is
``IcsSessionRetriever`` with a single preparatory step. Looking up a year
submits a form (POST) that stores the address in a server-side session, then
the actual ICS calendar is read back with a plain GET; both requests share
``source.session``, and the session cookie is what ties them together.
December also queries the following year, as the provider publishes it early;
unlike the current year (a genuine failure there is not swallowed), a failure
fetching the extra year is tolerated.

The legacy ``ICON_MAP`` mapped four raw ICS summaries to icons. Three already
match the shared multilingual vocabulary's German aliases exactly
("Biotonne", "Papiertonne", "Gelbe Tonne"); only "Hausmuelltonne" (an ASCII
transliteration without the umlaut) does not, so it is the sole explicit
override kept here — the rest resolve for free, non-lossy either way.
"""

from typing import ClassVar, final
from urllib.parse import urlencode

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://www.awv-ot.de/tourenauskunft/auskunftbatix.php"
_ICS_URL = "https://www.awv-ot.de/tourenauskunft/ics/ics.php"

_TYPE_VALUE_MAP = {
    "hausmuelltonne": GENERAL_WASTE,
}

# Every summary reads "Leerung <bin>"; the group is the bin, trimmed.
_SUMMARY_RE = r"^(?:Leerung)?\s*(.*?)\s*$"

_NO_ENTRIES = (
    "No entries found. Make sure the address matches exactly with an address "
    "suggested here: https://www.awv-ot.de/www/awvot/abfuhrtermine/leerungstage/"
)


def _address_form(year: int, city: str, street: str, hnr: str, **_) -> str:
    """The address form the servlet stores in the session, latin-1 as it wants."""
    return urlencode(
        {
            "JAHR": str(year),
            "Ort": city,
            "Strasse": street,
            "Step": "3",
            "HSN": hnr,
        },
        encoding="latin-1",
    )


@final
class Source(BaseSource):
    TITLE = "AWV: Abfall Wirtschaftszweckverband Ostthüringen"
    DESCRIPTION = "Source for AWV: Abfall Wirtschaftszweckverband Ostthüringen."
    URL = "https://www.awv-ot.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    # Only "Hausmuelltonne" is in the map above; the other three summaries
    # ("Biotonne", "Papiertonne", "Gelbe Tonne") resolve through the shared
    # vocabulary, so the auto-derived set would miss them. Declare the full
    # emittable vocabulary explicitly.
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Bethenhausen Caasen 15A": {
            "city": "Bethenhausen OT Caasen",
            "street": "Caasen",
            "hnr": "15A",
        },
        "Kraftsdorf OT Oberndorf, Klosterlausnitzer Straße 5/1": {
            "city": "Kraftsdorf OT Oberndorf",
            "street": "Klosterlausnitzer Straße",
            "hnr": "5/1",
        },
        "Gera, Aga Birkenstraße 9": {
            "city": "Gera",
            "street": "Aga Birkenstraße",
            "hnr": "9",
        },
    }

    PARAMS = (city(), street(), house_number("hnr"))

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "method": "POST",
                "url": _API_URL,
                "data": _address_form,
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            }
        ],
        feed_url=_ICS_URL,
        # A per-year emptiness check rather than a combined RAISE_ON_EMPTY at
        # the end of the pipeline: a genuine failure on the *current* year must
        # propagate even in December, before the following year is attempted.
        require_entries=True,
        empty_message=_NO_ENTRIES,
    )

    parse = IcsFeedsParser(parsers.IcsParser(regex=_SUMMARY_RE))

    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)

    def __init__(self, city: str, street: str, hnr: str):
        super().__init__(city=city, street=street, hnr=hnr)
