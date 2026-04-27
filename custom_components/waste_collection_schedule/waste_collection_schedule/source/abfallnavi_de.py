from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AbfallnaviDe import SERVICE_DOMAINS, AbfallnaviDe

TITLE = "AbfallNavi (RegioIT.de)"
TITLE_LANG = "de"
DESCRIPTION = (
    "Source for AbfallNavi waste collection. AbfallNavi is a brand name of regioit.de."
)
URL = "https://www.regioit.de"


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": s["url"],
            "default_params": {"service": s["service_id"]},
        }
        for s in SERVICE_DOMAINS
    ]


TEST_CASES = {
    "Aachen, Abteiplatz 7": {
        "service": "aachen",
        "city": "Aachen",
        "street": "Abteiplatz",
        "house_number": "7",
    },
    "Lindlar, Aggerweg": {
        "service": "bav",
        "city": "Lindlar",
        "street": "Aggerweg",
    },
    "Overath, Hauptstraße": {
        "service": "bav",
        "city": "Overath",
        "street": "Hauptstraße",
    },
    "Roetgen, Am Sportplatz 2": {
        "service": "zew2",
        "city": "Roetgen",
        "street": "Am Sportplatz",
        "house_number": "2",
    },
    "nds Norderstedt Adenauerplatz": {
        "service": "nds",
        "city": "Norderstedt",
        "street": "Distelweg",
    },
    "una Bergkamen, Agnes-Miegel-Str.": {
        "service": "unna",
        "city": "Bergkamen",
        "street": "Agnes-Miegel-Str.",
    },
    "Pinneberg Kummerfeld no Street": {
        "service": "pi",
        "city": "Kummerfeld",
        "street": "alle Straßen",
    },
    "Cuxhaven": {
        "service": "cux",
        "city": "Cuxhaven",
        "street": "Zur Holter Höhe",
    },
    "frankenthal, Am Martinspfad": {
        "service": "frankenthal",
        "city": "Frankenthal",
        "street": "Am Martinspfad",
    },
}


class Source:
    def __init__(
        self,
        service: str,
        city: str,
        street: str | None = None,
        house_number: str | int | None = None,
    ):
        self._api = AbfallnaviDe(service)
        self._ort = city
        self._strasse = street
        self._hausnummer = (
            str(house_number) if isinstance(house_number, int) else house_number
        )

    def fetch(self):
        dates = self._api.get_dates(self._ort, self._strasse, self._hausnummer)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return sorted(entries, key=lambda e: e.date)
