import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaftsverbandes Lippe"
DESCRIPTION = "Source for Abfallwirtschaftsverbandes Lippe."
URL = "https://abfall-lippe.de"
TEST_CASES = {
    "Bad Salzuflen BB": {"gemeinde": "Bad Salzuflen", "bezirk": "BB"},
    "Augustdorf": {"gemeinde": "Augustdorf"},
    "Barntrup 3B": {"gemeinde": "Barntrup", "bezirk": "3-B"},
}


ICON_MAP = {
    "Graue": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Grüne": "mdi:leaf",
    "Laubannahme": "mdi:leaf-maple",
    "Blaue": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
    "Schadstoffsammlung": "mdi:biohazard",
    "Groß-Container Altpapier|Pappe": "mdi:package-variant-closed",
}


API_URL = "https://abfall-lippe.de/service/abfuhrkalender/"


class Source:
    def __init__(self, gemeinde: str, bezirk: str | None = None):
        self._gemeinde: str = gemeinde
        self._bezirk: str = bezirk if bezirk is not None else ""
        self._ics = ICS()

    def fetch(self):

        r = requests.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        h3s = soup.find_all("h3")

        gemeinde = None
        for h3 in h3s:
            if not isinstance(h3, Tag):
                continue

            if h3.text.lower().strip() == self._gemeinde.lower().strip():
                gemeinde = h3
                break

        if gemeinde is None:
            raise Exception("Gemeinde not found, please check spelling")

        links_container = gemeinde.find_next_sibling("p")

        if not isinstance(links_container, Tag):
            raise Exception("No links found for gemeinde")

        link: Tag | None = None
        for a in links_container.find_all("a"):
            if not isinstance(a, Tag):
                continue
            if (
                a.text.lower().replace("ics", "").strip()
                == self._bezirk.lower().replace("ics", "").strip()
            ):
                link = a.get("href")
                break

        if link is None:
            raise Exception("Did not found matching ICS link for gemeinde and (bezirk)")

        # get ICS file
        r = requests.get(link)
        r.raise_for_status()
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            icon = ICON_MAP.get(d[1].split(" ")[0])
            if icon is None:
                icon = ICON_MAP.get(d[1])
            entries.append(Collection(d[0], d[1], icon=icon))

        return entries
