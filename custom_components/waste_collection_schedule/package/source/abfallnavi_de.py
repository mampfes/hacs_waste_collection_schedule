from collections import OrderedDict

from ..helpers import CollectionAppointment
from ..service.AbfallnaviDe import AbfallnaviDe


DESCRIPTION = "Source for AbfallNavi (= regioit.de) based services"
URL = "https://www.regioit.de"
TEST_CASES = OrderedDict(
    [
        (
            "Aachen, Abteiplatz 7",
            {"service": "aachen", "ort": "Aachen", "strasse": "Abteiplatz", "hausnummer": "7"},
        ),
        ("Lindlar, Aggerweg", {"service": "lindlar", "ort": "Lindlar", "strasse": "Aggerweg"}),
        ("Roetgen, Am Sportplatz 2", {"service": "roe", "ort": "Roetgen", "strasse": "Am Sportplatz", "hausnummer": "2"}),
    ]
)


class Source:
    def __init__(self, service, ort, strasse, hausnummer=None):
        self._api = AbfallnaviDe(service)
        self._ort = ort
        self._strasse = strasse
        self._hausnummer = hausnummer

    def fetch(self):
        dates = self._api.get_dates(self._ort, self._strasse, self._hausnummer)

        entries = []
        for d in dates:
            entries.append(CollectionAppointment(d[0], d[1]))
        return entries
