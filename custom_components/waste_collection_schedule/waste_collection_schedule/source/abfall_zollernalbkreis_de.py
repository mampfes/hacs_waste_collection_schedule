import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Zollernalbkreis"
DESCRIPTION = "Source for Abfallwirtschaft Zollernalbkreis waste collection."
URL = "https://www.abfallkalender-zak.de"
TEST_CASES = {
    "Ebingen": {
        "city": "2,3,4",
        "street": "3",
    },
    "Erlaheim": {
        "city": "79",
        "street": "",
    },
    "Ebingen names": {
        "city": "Ebingen",
        "street": "Am schnecklesfelsen",
    },
    "Schlatt names": {
        "city": "Schlatt",
    },
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Grünabfall": "mdi:leaf",
    "Biomüll": "mdi:leaf",
    "Gelber Sack": "mdi:sack",
    "Papiertonne": "mdi:package-variant",
    "Bildschirm-/Kühlgeräte": "mdi:television-classic",
    "Schadstoffsammlung": "mdi:biohazard",
    "altmetalle": "mdi:nail",
}

LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, city, types=None, street=None):
        self._city = city
        self._street = street
        if types:
            LOGGER.warning(
                "you provided types parameter but filtering should be done by using the customize argument. Ignoring types"
            )

        self._ics = ICS()

    def get_ids(self, soup, id, copmare):
        options = soup.find("select", id=id).findAll("option")
        for option in options:
            if option.text.lower().strip() == copmare.lower().strip():
                return option["value"]
        raise Exception(f"{id.capitalize()} {copmare} not found")

    def fetch(self):
        r = requests.get("https://www.abfallkalender-zak.de")
        soup = BeautifulSoup(r.text, "html.parser")
        types = [t["value"] for t in soup.findAll("input", attrs={"name": "types[]"})]

        if not self._city.replace(" ", "").replace(",", "").isnumeric():
            # city is not a number, so we need to get the id
            self._city = self.get_ids(soup, "city", self._city)
        if (
            self._street
            and not self._city.replace(" ", "").replace(",", "").isnumeric()
        ):
            # city is not a number, so we need to get the id
            self._street = self.get_ids(soup, "street", self._street)

        now = datetime.now()
        entries = self.fetch_year(now.year, self._city, self._street, types)
        if now.month == 12:
            # also get data for next year if we are already in december
            try:
                entries.extend(
                    self.fetch_year((now.year + 1), self._city, self._street, types)
                )
            except Exception:
                # ignore if fetch for next year fails
                pass
        return entries

    def fetch_year(self, year, city, street, types):
        args = {
            "city": city,
            "street": street,
            "year": year,
            "types[]": types,
            "go_ics": "Download",
        }

        # get ics file
        r = requests.get("https://www.abfallkalender-zak.de", params=args)

        # parse ics file
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            waste_type = d[1]
            next_pickup_date = d[0]

            entries.append(
                Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.split(" ")[0]),
                )
            )

        return entries
