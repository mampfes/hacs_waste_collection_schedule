from datetime import datetime
from difflib import get_close_matches

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "CEM Ambiente"
DESCRIPTION = "Source for CEM Ambiente (CEM FACILE), covering municipalities in the Milano / Monza e Brianza / Lodi area of Italy."
URL = "https://www.cemambiente.it"
COUNTRY = "it"

API_URL = "https://cemfacile.cemambiente.it"

EXTRA_INFO = [
    {"title": "Agrate Brianza", "country": "it"},
    {"title": "Aicurzio", "country": "it"},
    {"title": "Arcore", "country": "it"},
    {"title": "Basiano", "country": "it"},
    {"title": "Bellinzago Lombardo", "country": "it"},
    {"title": "Bellusco", "country": "it"},
    {"title": "Bernareggio", "country": "it"},
    {"title": "Borgo San Giovanni", "country": "it"},
    {"title": "Brugherio", "country": "it"},
    {"title": "Burago Di Molgora", "country": "it"},
    {"title": "Busnago", "country": "it"},
    {"title": "Bussero", "country": "it"},
    {"title": "Cambiago", "country": "it"},
    {"title": "Camparada", "country": "it"},
    {"title": "Caponago", "country": "it"},
    {"title": "Carnate", "country": "it"},
    {"title": "Carpiano", "country": "it"},
    {"title": "Carugate", "country": "it"},
    {"title": "Casaletto Lodigiano", "country": "it"},
    {"title": "Casalmaiocco", "country": "it"},
    {"title": "Caselle Lurani", "country": "it"},
    {"title": "Cassano D'Adda", "country": "it"},
    {"title": "Cassina De' Pecchi", "country": "it"},
    {"title": "Cavenago Di Brianza", "country": "it"},
    {"title": "Cernusco Sul Naviglio", "country": "it"},
    {"title": "Cerro Al Lambro", "country": "it"},
    {"title": "Cervignano D'Adda", "country": "it"},
    {"title": "Cologno Monzese", "country": "it"},
    {"title": "Colturano", "country": "it"},
    {"title": "Comazzo", "country": "it"},
    {"title": "Concorezzo", "country": "it"},
    {"title": "Cornate D'Adda", "country": "it"},
    {"title": "Correzzana", "country": "it"},
    {"title": "Dresano", "country": "it"},
    {"title": "Gessate", "country": "it"},
    {"title": "Gorgonzola", "country": "it"},
    {"title": "Grezzago", "country": "it"},
    {"title": "Inzago", "country": "it"},
    {"title": "Lesmo", "country": "it"},
    {"title": "Liscate", "country": "it"},
    {"title": "Macherio", "country": "it"},
    {"title": "Masate", "country": "it"},
    {"title": "Massalengo", "country": "it"},
    {"title": "Mediglia", "country": "it"},
    {"title": "Melegnano", "country": "it"},
    {"title": "Melzo", "country": "it"},
    {"title": "Merlino", "country": "it"},
    {"title": "Mezzago", "country": "it"},
    {"title": "Mulazzano", "country": "it"},
    {"title": "Ornago", "country": "it"},
    {"title": "Pantigliate", "country": "it"},
    {"title": "Paullo", "country": "it"},
    {"title": "Pessano Con Bornago", "country": "it"},
    {"title": "Pozzo D'Adda", "country": "it"},
    {"title": "Pozzuolo Martesana", "country": "it"},
    {"title": "Rodano", "country": "it"},
    {"title": "Roncello", "country": "it"},
    {"title": "Ronco Briantino", "country": "it"},
    {"title": "Salerano sul Lambro", "country": "it"},
    {"title": "San Zenone Al Lambro", "country": "it"},
    {"title": "Sant'Angelo Lodigiano", "country": "it"},
    {"title": "Settala", "country": "it"},
    {"title": "Sordio", "country": "it"},
    {"title": "Sulbiate", "country": "it"},
    {"title": "Torrevecchia Pia", "country": "it"},
    {"title": "Trezzano Rosa", "country": "it"},
    {"title": "Trezzo Sull'Adda", "country": "it"},
    {"title": "Tribiano", "country": "it"},
    {"title": "Truccazzano", "country": "it"},
    {"title": "Usmate Velate", "country": "it"},
    {"title": "Vaprio D'Adda", "country": "it"},
    {"title": "Vedano Al Lambro", "country": "it"},
    {"title": "Vignate", "country": "it"},
    {"title": "Villasanta", "country": "it"},
    {"title": "Vimercate", "country": "it"},
    {"title": "Vimodrone", "country": "it"},
    {"title": "Vizzolo Predabissi", "country": "it"},
]

TEST_CASES = {
    "Vimodrone, Via Aldo Moro": {"city": "Vimodrone", "street": "Via Aldo Moro"},
    "Cologno Monzese, Via Cadore": {"city": "Cologno Monzese", "street": "Via Cadore"},
    "Vimercate, Via Cesare Battisti": {
        "city": "Vimercate",
        "street": "Via Cesare Battisti",
    },
}

ICON_MAP = {
    "UMI": Icons.BIO_KITCHEN,  # Raccolta Umido (food waste)
    "VER": Icons.GARDEN,  # Raccolta Verde (garden waste)
    "CAR": Icons.PAPER,  # Raccolta Carta
    "VET": Icons.GLASS,  # Raccolta Vetro
    "MUL": Icons.PLASTIC_PACKAGING,  # Raccolta Multipak (plastic + metal)
    "APL": Icons.PLASTIC_PACKAGING,  # Raccolta Altre Plastiche
    "SEC": Icons.GENERAL_WASTE,  # Raccolta Secco
    "ECU": Icons.GENERAL_WASTE,  # Raccolta Ecuosacco
    "STP": Icons.GENERAL_WASTE,  # Raccolta Ecuosacco puntuale
}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the municipality (comune) and street (via) exactly as they are "
    "known to CEM Ambiente, e.g. as shown on https://www.cemambiente.it/cemfacile/. "
    "If the exact spelling isn't found, the error message will list the closest "
    "matching street names for your municipality.",
    "it": "Inserisci il comune e la via esattamente come sono indicati da CEM "
    "Ambiente, ad esempio come mostrato su https://www.cemambiente.it/cemfacile/. "
    "Se l'ortografia esatta non viene trovata, il messaggio di errore elencherà le "
    "vie più simili per il tuo comune.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "The municipality served by CEM Ambiente (e.g. 'Vimodrone').",
        "street": "The street name as listed by CEM Ambiente for the selected "
        "municipality (e.g. 'Via Aldo Moro').",
    },
    "it": {
        "city": "Il comune servito da CEM Ambiente (ad esempio 'Vimodrone').",
        "street": "Il nome della via come indicato da CEM Ambiente per il comune "
        "selezionato (ad esempio 'Via Aldo Moro').",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
    },
    "it": {
        "city": "Comune",
        "street": "Via",
    },
}


class Source:
    def __init__(self, city: str, street: str):
        self._city: str = city
        self._street: str = street

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        r = session.post(f"{API_URL}/public/listComuni", json={})
        r.raise_for_status()
        comuni = r.json().get("body", [])

        comune = next(
            (
                c
                for c in comuni
                if str(c.get("nome", "")).casefold() == self._city.strip().casefold()
            ),
            None,
        )
        if comune is None:
            all_names = [c.get("nome", "") for c in comuni]
            suggestions = get_close_matches(self._city, all_names, n=5, cutoff=0.4)
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, suggestions or sorted(all_names)
            )

        id_siunet = comune["idSiunet"]

        r = session.post(f"{API_URL}/public/listVie", json={"idSiunet": id_siunet})
        r.raise_for_status()
        vie = r.json().get("body", [])

        via = next(
            (
                v
                for v in vie
                if str(v.get("nome", "")).casefold() == self._street.strip().casefold()
            ),
            None,
        )
        if via is None:
            all_streets = [v.get("nome", "") for v in vie]
            suggestions = get_close_matches(self._street, all_streets, n=5, cutoff=0.4)
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions or sorted(all_streets)
            )

        r = session.post(
            f"{API_URL}/public/getCalendario",
            json={
                "idSiunet": id_siunet,
                "idVia": via["idVia"],
                "nomeVia": via["nome"],
            },
        )
        r.raise_for_status()
        servizi = r.json().get("body", [])

        entries: list[Collection] = []
        for item in servizi:
            date_str = item.get("data")
            servizio = item.get("servizio")
            if not date_str or not servizio:
                continue

            date = datetime.fromisoformat(date_str).date()

            tipologia = item.get("tipologiaServizio") or ""
            code = tipologia.split(" - ")[0].strip()
            icon = ICON_MAP.get(code)

            entries.append(Collection(date=date, t=servizio, icon=icon))

        return entries
