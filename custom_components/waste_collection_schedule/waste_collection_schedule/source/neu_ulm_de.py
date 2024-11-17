import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ICS import ICS

TITLE = "Neu-Ulm"
DESCRIPTION = "Source for Neu-Ulm."
URL = "https://nu.neu-ulm.de/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender"
TEST_CASES = {
    "Bezirk 1": {"region": "Bezirk 1"},
    "Bezirk 8": {"region": "Bezirk 8"},
    # "Bezirk failure": {"region": "Bezirk failure"},
}
COUNTRY = "de"

ICON_MAP = {
    "Gelber Sack": "mdi:recycle",
    "Grüngut": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Rest- und Biomüll": "mdi:trash-can",
    "Wertstoffhof geschlossen": "mdi:factory",
}


HOST_URI = "https://nu.neu-ulm.de"

PARAM_TRANSLATIONS = {
    "de": {
        "region": "Bezirk",
    }
}


class Source:
    def __init__(self, region: str):
        self._region: str = region

    def fetch(self) -> list[Collection]:
        # get json file
        r = requests.get(
            f"{HOST_URI}/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender"
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        ics_link = soup.find(lambda tag: tag.name == "a" and self._region in tag.text)

        if ics_link:
            r = requests.get(f"{HOST_URI}{ics_link['href']}")
            r.raise_for_status()

            ics = ICS()
            dates = ics.convert(r.text)

            entries = []
            for d in dates:
                text = d[1].strip().replace("Abfuhr ", "")
                entries.append(
                    Collection(
                        date=d[0],
                        t=text,
                        icon=ICON_MAP.get(text),
                    )
                )

            return entries

        raise SourceArgumentNotFound(
            "region",
            self._region,
            "Check the available Bezirke on https://nu.neu-ulm.de/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender",
        )
