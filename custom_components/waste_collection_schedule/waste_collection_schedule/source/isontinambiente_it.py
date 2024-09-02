import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "isontina ambiente: Ronchi dei legionari"
DESCRIPTION = "Source for isontina ambiente, serving Ronchi dei legionari."
URL = "https://isontinambiente.it"
TEST_CASES = {
    "PIAZZA FURLAN, Ronchi dei Legionari Area B": {"address_id": 1172},
    "VIA DANTE  , Ronchi dei Legionari Area C": {"address_id": 75},
    "VIA GORIZIA  , Ronchi dei Legionari Area F": {"address_id": 147},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari> and select your address. The address ID is the number at the end of the URL. e.g. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/?indirizzo=1172` the address ID is `1172`.",
    "it": "Visita <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari> e seleziona il tuo indirizzo. L'ID dell'indirizzo è il numero alla fine dell'URL. es. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/?indirizzo=1172` l'ID dell'indirizzo è `1172`.",
}


ICON_MAP = {
    "Plastica e lattine": "mdi:recycle",
    "Organico umido": "mdi:leaf",
    "Carta e cartone": "mdi:package-variant",
    "Secco residuo": "mdi:trash-can",
}

ITALIAN_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}


API_URL = "https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/"


class Source:
    def __init__(self, address_id: str | int):
        self._address_id: str | int = address_id

    def fetch(self) -> list[Collection]:
        args = {"indirizzo": self._address_id}

        # get json file
        r = requests.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        calendars = soup.select("table.calendar")

        collections = []
        for (
            calendar
        ) in (
            calendars
        ):  # Probably only one but just in case there are more at the end of a month
            prev_sibling = calendar.find_previous_sibling()
            if not isinstance(prev_sibling, Tag):
                raise Exception("Cannot find calendar header")

            if not prev_sibling.name == "h3":
                prev_sibling = prev_sibling.select_one("h3")
            if not prev_sibling:
                raise Exception("Cannot find calendar header")
            header = prev_sibling.text.strip()

            italian_month, year_str = header.split(" ")
            month = ITALIAN_MONTHS[italian_month.lower()]
            try:
                year = int(year_str)
            except ValueError:
                raise Exception(f"Cannot parse year: {year_str}")

            legend = calendar.find_next_sibling()
            if not isinstance(legend, Tag):
                raise Exception("Cannot find calendar legend")

            names: dict[str, str] = {}
            for div in legend.select("div"):
                classes = div.select_one("span.dot")["class"]
                classes.remove("dot")
                names[classes[0]] = div.text.strip()

            for td in calendar.select("td"):
                for dot in td.select("div.dot"):
                    if not dot:
                        continue

                    classes = dot.attrs["class"]
                    classes.remove("dot")
                    bin_type = names.get(classes[0], classes[0])

                    collections.append(
                        Collection(
                            date=datetime.date(year, month, int(td.text)),
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type),
                        )
                    )

        return collections
