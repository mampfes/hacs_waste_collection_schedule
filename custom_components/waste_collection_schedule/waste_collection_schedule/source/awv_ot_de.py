"""AWV: Abfall Wirtschaftszweckverband Ostthüringen.

Demonstrates: the "year-window, stateful POST-then-GET" shape. Looking up a
year submits a form (POST) that stores the address in a server-side session,
then the actual ICS calendar is read back with a plain GET; both requests
must share cookies, so ``retrieve`` uses ``self.session`` for both. December
also queries the following year, as the provider publishes it early; unlike
the current year (a genuine failure there is not swallowed), a failure
fetching the extra year is tolerated, matching the legacy source exactly.

The legacy ``ICON_MAP`` mapped four raw ICS summaries to icons. Three already
match the shared multilingual vocabulary's German aliases exactly
("Biotonne", "Papiertonne", "Gelbe Tonne"); only "Hausmuelltonne" (an ASCII
transliteration without the umlaut) does not, so it is the sole explicit
override kept here — the rest resolve for free, non-lossy either way.
"""

import datetime
from typing import ClassVar, final
from urllib.parse import urlencode

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

_API_URL = "https://www.awv-ot.de/tourenauskunft/auskunftbatix.php"
_ICS_URL = "https://www.awv-ot.de/tourenauskunft/ics/ics.php"

_TYPE_VALUE_MAP = {
    "hausmuelltonne": GENERAL_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "AWV: Abfall Wirtschaftszweckverband Ostthüringen"
    DESCRIPTION = "Source for AWV: Abfall Wirtschaftszweckverband Ostthüringen."
    URL = "https://www.awv-ot.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

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

    def retrieve(self, source):
        now = datetime.datetime.now()
        years = [now.year, now.year + 1] if now.month == 12 else [now.year]

        texts: list[str] = []
        for i, year in enumerate(years):
            try:
                texts.append(self._fetch_year(year))
            except Exception:
                if i == 0:
                    raise
        return texts

    def _fetch_year(self, year: int) -> str:
        args = {
            "JAHR": str(year),
            "Ort": self.params["city"],
            "Strasse": self.params["street"],
            "Step": "3",
            "HSN": self.params["hnr"],
        }
        r = self.session.post(
            _API_URL,
            data=urlencode(args, encoding="latin-1"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        r = self.session.get(_ICS_URL)
        r.raise_for_status()
        text = r.text
        if not ICS().convert(text):
            # Matches the legacy per-year emptiness check exactly (rather than
            # a combined RAISE_ON_EMPTY at the end of the pipeline): a genuine
            # failure on the *current* year must propagate even in December,
            # before the following year is ever attempted.
            raise ValueError(
                "No entries found. Make sure the address matches exactly "
                "with an address suggested here: "
                "https://www.awv-ot.de/www/awvot/abfuhrtermine/leerungstage/"
            )
        return text

    def parse(self, response, source=None):
        entries: list = []
        for text in response:
            for date, summary in ICS().convert(text):
                entries.append((date, summary.removeprefix("Leerung").strip()))
        return entries

    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)

    def __init__(self, city: str, street: str, hnr: str):
        super().__init__(city=city, street=street, hnr=hnr)
