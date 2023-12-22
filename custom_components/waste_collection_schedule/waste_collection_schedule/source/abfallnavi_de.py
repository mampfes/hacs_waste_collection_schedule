from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AbfallnaviDe import (
    SERVICE_DOMAINS,
    AbfallnaviDe,
)

TITLE = "AbfallNavi (RegioIT.de)"
DESCRIPTION = (
    "Source for AbfallNavi waste collection. AbfallNavi is a brand name of regioit.de."
)
URL = "https://www.regioit.de"


def EXTRA_INFO():
    return [{"title": s["title"], "url": s["url"]} for s in SERVICE_DOMAINS]


TEST_CASES = {
    "Aachen, Abteiplatz 7": {
        "service": "aachen",
        "ort": "Aachen",
        "strasse": "Abteiplatz",
        "hausnummer": "7",
    },
    "Lindlar, Aggerweg": {
        "service": "lindlar",
        "ort": "Lindlar",
        "strasse": "Aggerweg",
    },
    "Roetgen, Am Sportplatz 2": {
        "service": "zew2",
        "ort": "Roetgen",
        "strasse": "Am Sportplatz",
        "hausnummer": "2",
    },
    "nds Norderstedt Adenauerplatz": {
        "service": "nds",
        "ort": "Norderstedt",
        "strasse": "Distelweg",
    },
    "una Bergkamen, Agnes-Miegel-Str.": {
        "service": "unna",
        "ort": "Bergkamen",
        "strasse": "Agnes-Miegel-Str.",
    },
}


class Source:
    def __init__(
        self, service: str, ort: str, strasse: str, hausnummer: str | int | None = None
    ):
        self._api = AbfallnaviDe(service)
        self._ort = ort
        self._strasse = strasse
        self._hausnummer = (
            str(hausnummer) if isinstance(hausnummer, int) else hausnummer
        )

    def fetch(self):
        dates = self._api.get_dates(self._ort, self._strasse, self._hausnummer)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return sorted(entries, key=lambda e: e.date)
