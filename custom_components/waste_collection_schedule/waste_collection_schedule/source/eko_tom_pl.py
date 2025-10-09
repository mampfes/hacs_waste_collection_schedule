# This source uses the already existing API for c_trace but with some name changes and it does not use the ical file, so it got its own source file.

import datetime
import logging

import requests as req
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOOGGER = logging.getLogger(__name__)

TITLE = "Czerwonak, Murowana Goślina, Oborniki"
DESCRIPTION = (
    "Source for eko-tom.pl. Municipalities: Czerwonak, Murowana Goślina, Oborniki"
)
URL = "https://www.eko-tom.pl"

TEST_CASES = {
    "Czerwonak": {"city": "Czerwonak", "street": "Źródlana", "nr": "39"},
    "BIAŁĘŻYN": {"city": "BIAŁĘŻYN", "street": "BIAŁĘŻYN", "nr": "1/A"},
}

API_URL = "https://web.c-trace.de/ekotom-abfallkalender/(S(y0ommq52pdbwa0jek4oqqzgr))/kalendarzodpadow/abc?Ort={city}&Strasse={street}&Hausnr={nr}"

ICON_MAP = {
    "Zmieszane": "mdi:trash-can",  # Mixed
    "Tworzywa": "mdi:recycle",  # Plastic
    "BIO": "mdi:leaf",  # Organic
    "Papier": "mdi:file-outline",  # Paper
    "Szkło": "mdi:glass-fragile",  # Glass
    "Gabaryty": "mdi:dump-truck",  # Bulky Waste
}


class Source:
    def __init__(self, street, city, nr):
        self._city = city
        self._street = street
        self._nr = nr

    def fetch(self):
        address = API_URL.format(city=self._city, street=self._street, nr=self._nr)
        response = req.get(address)

        if response.status_code != 200:
            print(f"Error fetching data from {address}: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        waste_types = {
            "plan rest clear": "Zmieszane",
            "glas": "Szkło",
            "plastik": "Tworzywa",
            "bio": "BIO",
            "papier": "Papier",
            "plan sperr clear": "Gabaryty",
        }

        for waste_class, waste_type in waste_types.items():
            try:
                for li in soup.find(class_=waste_class).find_all("li"):
                    date_text = li.text.strip()
                    date_format = "%d.%m.%Y"
                    cleaned_date_text = (
                        date_text.replace("\r", "")
                        .replace("\n", "")
                        .replace("pon.,", "")
                        .replace("wt.,", "")
                        .replace("sr.,", "")
                        .replace("śr.,", "")
                        .replace("czw.,", "")
                        .replace("pt.,", "")
                        .replace("sob.,", "")
                        .replace("nie.,", "")
                        .strip()
                    )
                    date_str = str(
                        datetime.datetime.strptime(
                            cleaned_date_text, date_format
                        ).date()
                    )

                    try:
                        entries.append(
                            Collection(
                                date=datetime.datetime.strptime(
                                    date_str, "%Y-%m-%d"
                                ).date(),
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )

                    except ValueError:
                        _LOOGGER.debug(f"Error converting date string: {date_text}")

            except AttributeError:
                _LOOGGER.debug(f"No data found for waste type: {waste_type}")

        return entries
