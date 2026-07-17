import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Isontina Ambiente"
DESCRIPTION = "Source for Isontina Ambiente, serving municipalities in the province of Gorizia, Italy."
URL = "https://isontinambiente.it"
TEST_CASES = {
    "PIAZZA FURLAN, Ronchi dei Legionari Area B": {"address_id": 1172},
    "VIA DANTE, Ronchi dei Legionari Area C": {
        "city": "ronchi-dei-legionari",
        "address_id": 75,
    },
    "ANDRONA DELLA PERGOLA, Gorizia Area B": {"city": "Gorizia", "address_id": 488},
    "ANDRONA AQUILEIA, Monfalcone Area Monfalcone Ovest": {
        "city": "monfalcone",
        "address_id": 819,
    },
    "Capriva del Friuli (single zone)": {"city": "capriva-del-friuli"},
    "Villesse (single zone)": {"city": "villesse"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/> and select your municipality. The `city` argument is the last part of the URL, e.g. for `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/gorizia/` the `city` is `gorizia`. If your municipality's page shows an address dropdown, also select your address there; the `address_id` is the number at the end of the URL, e.g. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/gorizia/?indirizzo=488` the `address_id` is `488`. If there is no address dropdown, `address_id` can be omitted.",
    "it": "Visita <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/> e seleziona il tuo comune. L'argomento `city` è l'ultima parte dell'URL, es. per `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/gorizia/` il `city` è `gorizia`. Se la pagina del tuo comune mostra un menu per selezionare l'indirizzo, seleziona anche il tuo indirizzo; l'ID dell'indirizzo è il numero alla fine dell'URL, es. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/gorizia/?indirizzo=488` l'ID dell'indirizzo è `488`. Se non è presente un menu per l'indirizzo, `address_id` può essere omesso.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "Municipality",
        "address_id": "Address ID",
    },
    "it": {
        "city": "Comune",
        "address_id": "ID indirizzo",
    },
    "de": {
        "city": "Gemeinde",
        "address_id": "Adress-ID",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "The municipality slug, see 'How to get the source argument'.",
        "address_id": "The address ID, see 'How to get the source argument'. Not required for municipalities without an address selection.",
    },
    "it": {
        "city": "Lo slug del comune, vedi 'Come ottenere l'argomento'.",
        "address_id": "L'ID dell'indirizzo, vedi 'Come ottenere l'argomento'. Non richiesto per i comuni senza selezione dell'indirizzo.",
    },
    "de": {
        "city": "Der Gemeinde-Slug, siehe 'Wie man das Quellenargument erhält'.",
        "address_id": "Die Adress-ID, siehe 'Wie man das Quellenargument erhält'. Nicht erforderlich für Gemeinden ohne Adressauswahl.",
    },
}


ICON_MAP = {
    "Plastica e lattine": Icons.RECYCLING,
    "Organico umido": Icons.BIO_KITCHEN,
    "Carta e cartone": Icons.PAPER,
    "Secco residuo": Icons.GENERAL_WASTE,
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

# Municipalities served by Isontina Ambiente that expose a collection
# calendar. `Duino Aurisina` is deliberately excluded: it is served by
# street-side bins ("cassonetti di prossimità") and has no calendar page.
CITIES = {
    "capriva-del-friuli": "Capriva del Friuli",
    "cormons": "Cormons",
    "doberdo-del-lago": "Doberdò del Lago",
    "dolegna-del-collio": "Dolegna del Collio",
    "farra-disonzo": "Farra d'Isonzo",
    "fogliano-redipuglia": "Fogliano Redipuglia",
    "gorizia": "Gorizia",
    "gradisca-disonzo": "Gradisca d'Isonzo",
    "grado": "Grado",
    "mariano-del-friuli": "Mariano del Friuli",
    "medea": "Medea",
    "monfalcone": "Monfalcone",
    "monrupino": "Monrupino",
    "moraro": "Moraro",
    "mossa": "Mossa",
    "romans-disonzo": "Romans d'Isonzo",
    "ronchi-dei-legionari": "Ronchi dei Legionari",
    "sagrado": "Sagrado",
    "san-canzian-disonzo": "San Canzian d'Isonzo",
    "san-floriano-del-collio": "San Floriano del Collio",
    "san-lorenzo-isontino": "San Lorenzo Isontino",
    "san-pier-disonzo": "San Pier d'Isonzo",
    "savogna-disonzo": "Savogna d'Isonzo",
    "sgonico-zgonik": "Sgonico - Zgonik",
    "staranzano": "Staranzano",
    "turriaco": "Turriaco",
    "villesse": "Villesse",
}


API_URL = "https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/{city}/"


class Source:
    def __init__(
        self,
        address_id: str | int | None = None,
        city: str = "ronchi-dei-legionari",
    ):
        city_normalized = city.strip().lower().replace(" ", "-")
        if city_normalized not in CITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", city, list(CITIES.keys())
            )
        self._city: str = city_normalized
        self._address_id: str | int | None = address_id

    def fetch(self) -> list[Collection]:
        args = {}
        if self._address_id is not None:
            args["indirizzo"] = self._address_id

        # get calendar page
        r = requests.get(API_URL.format(city=self._city), params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        calendars = soup.select("table.calendar")

        collections = []
        for calendar in (
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
                raise Exception(f"Cannot parse year: {year_str}") from None

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
