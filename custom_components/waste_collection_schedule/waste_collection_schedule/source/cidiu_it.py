import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "CIDIU S.p.A."
DESCRIPTION = "Source for CIDIU waste collection services for the north-west Turin province"
URL = "https://cidiu.it/"

TEST_CASES = {
    "Collegno": {
        "city": "COLLEGNO",
        "street": "VIA CONDOVE",
        "street_number": "107",
    },

    "Grugliasco": {
        "city": "GRUGLIASCO",
        "street": "VIALE GRAMSCI",
        "street_number": "18",
    },

    "Rivoli": {
        "city": "RIVOLI",
        "street": "CORSO SUSA",
        "street_number": "124",
    },
}

ICON_MAP = {
    "INDIFFERENZIATO": "mdi:trash-can",
    "ORGANICO": "mdi:food-apple",
    "VETRO E LATTINE": "mdi:bottle-wine",
    "CARTA": "mdi:newspaper-variant-multiple",
    "PLASTICA": "mdi:recycle",
    "SFALCI ABBONAMENTO NORMALE": "mdi:leaf-cricle",
    "SFALCI ABBONAMENTO RIDOTTO": "mdi:leaf-circle-outline"
}

API_URL = "https://cidiu.it/wp-content/themes/icelander/integrazione-lista/cidiu-processer.php"

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html',
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street, street_number, city):
        self._street = street.upper()
        self._street_number = street_number.upper()
        self._city = city.upper()

    def fetch(self):
        session = requests.Session()
        params = {
            "func": "getrecollection",
            "comune": self._city,
            "indirizzo": self._street,
            "civico": self._street_number
        }

        r = session.get(
            API_URL, headers=HEADERS, params=params
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        rows = soup.find_all('tr')

        header_row = rows[0]
        headers = [th.text.strip() for th in header_row.find_all(
            ['th', 'td'])][1:]  # Skip the first empty header

        entries = []
        for row in rows[1:]:  # Skip the header row
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            date_cell = cells[0].text.strip()
            if ',' not in date_cell:
                logging.warning(f"Unexpected date format: {date_cell}")
                continue

            # date format is "11/08/2024, Domenica" - we can get rid of the italian day name
            date_str, day = date_cell.split(', ')
            try:
                date = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                logging.warning(f"Could not parse date: {date_str}")
                continue

            collections = []
            for header, cell in zip(headers, cells[1:]):
                if cell.text.strip():
                    collections.append(header)

            for collection in collections:
                entries.append(
                    Collection(
                        date=date,
                        t=collection.capitalize(),
                        icon=ICON_MAP.get(collection.upper())
                    ),
                )

        return entries
