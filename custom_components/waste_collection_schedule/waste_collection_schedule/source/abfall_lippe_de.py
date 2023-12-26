import datetime

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


API_URL = "https://abfall-lippe.de/service/abfuhrkalender"


class WrongURLError(Exception):
    pass


class Source:
    def __init__(self, gemeinde: str, bezirk: str | None = None):
        self._gemeinde: str = gemeinde
        self._bezirk: str = bezirk if bezirk is not None else ""
        self._ics = ICS()

    def fetch(self):
        now = datetime.datetime.now()
        year = now.year

        try:
            entries = self.get_data(API_URL)
        except WrongURLError:
            entries = self.get_data(f"{API_URL}-{year}")

        if now.month == 12:
            try:
                entries += self.get_data(f"{API_URL}-{year +1 }")
            except WrongURLError:
                pass
        if now.month == 1:
            try:
                entries += self.get_data(f"{API_URL}-{year -1 }")
            except WrongURLError:
                pass
        return entries

    def get_data(self, url):
        r = requests.get(url)
        if r.status_code != 200 or r.request.url == "https://abfall-lippe.de":
            raise WrongURLError("Fetch failed wrong ULR")

        soup = BeautifulSoup(r.text, "html.parser")
        headlines = soup.find_all("div", class_="elementor-widget-heading")

        gemeinde_headline: Tag | None = None
        for headline in headlines:
            if not isinstance(headline, Tag):
                continue
            h3 = headline.find("h3")
            if not isinstance(h3, Tag):
                continue

            if h3.text.lower().strip() == self._gemeinde.lower().strip():
                gemeinde_headline = headline
                break

        if gemeinde_headline is None:
            raise Exception("Gemeinde not found, please check spelling")

        links_container = gemeinde_headline.parent

        if links_container is None:
            raise Exception(f"No links found for {self._gemeinde}")

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
