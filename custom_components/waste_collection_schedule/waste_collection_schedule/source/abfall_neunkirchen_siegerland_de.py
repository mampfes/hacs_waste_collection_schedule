import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Neunkirchen Siegerland"
DESCRIPTION = " Source for 'Abfallkalender Neunkirchen Siegerland'."
URL = "https://www.neunkirchen-siegerland.de"
TEST_CASES = {"Waldstraße": {"strasse": "Waldstr"}}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, strasse):
        self._strasse = strasse
        self._ics = ICS()

    def fetch(self):
        args = {
            "out": "json",
            "type": "abto",
            "select": "2",
            "refid": "3362.1",
            "term": self._strasse,
        }
        header = {"referer": "https://www.neunkirchen-siegerland.de"}
        r = requests.get(
            "https://www.neunkirchen-siegerland.de/output/autocomplete.php",
            params=args,
            headers=header,
        )
        r.raise_for_status()

        ids = r.json()
        print(ids)

        if len(ids) == 0:
            raise Exception("no address found")

        if len(ids) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "strasse", self._strasse, [id[1] for id in ids]
            )

        args = {"ModID": 48, "call": "ical", "pois": ids[0][0], "kat": 1, "alarm": 0}
        r = requests.get(
            "https://www.neunkirchen-siegerland.de/output/options.php",
            params=args,
            headers=header,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return entries
