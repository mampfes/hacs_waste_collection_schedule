import datetime
import json
import logging

import requests
from waste_collection_schedule import Collection

TITLE = "Il Rifiutologo"
DESCRIPTION = "Source for ilrifiutologo.it"
URL = "https://ilrifiutologo.it"
COUNTRY = "it"
TEST_CASES = {
    "Test1": {"town": "Faenza", "street": "VIA AUGUSTO RIGHI", "house_number": "6"},
    "Test2": {"town": "Faenza", "street": "VIA AUGUSTO RIGHI", "house_number": 1},
}

API_URL = "https://www.ilrifiutologo.it/ajax/archivio_ilrifiutologo_ajax.php"
API_URL_BACKEND = "https://webapp-ambiente.gruppohera.it/rifiutologo/rifiutologoweb"
HEADERS = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Host": "www.ilrifiutologo.it",
    "Origin": "https://www.ilrifiutologo.it",
    "Referer": "http://www.ilrifiutologo.it/casa_rifiutologo/",
    "X-Requested-With": "XMLHttpRequest",
}

ICON_MAP = {
    "Lattine": "mdi:bottle-soda-classic",
    "Plastica": "mdi:bottle-soda-classic",
    "Indifferenziato": "mdi:trash-can",
    "Vetro": "mdi:glass-fragile",
    "Organico": "mdi:apple",
    "Sfalci e potature": "mdi:leaf",
    "Pannolini/Pannoloni": "mdi:baby-carriage",
    "Carta e cartone": "mdi:newspaper",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self, town: str, street: str, house_number: int | str
    ):  # argX correspond to the args dict in the source configuration
        self.comune_id = None
        self.inirizzo_id = None
        self.civico_id = None

        comuni = api_get_request(relative_path="/getComuni.php")
        _LOGGER.debug(
            "getComuni.php: %d s - %s - %s",
            comuni.elapsed.total_seconds(),
            comuni.status_code,
            comuni.reason,
        )

        if comuni.status_code != 200 or not isinstance(comuni.json(), list):
            raise Exception("Errore durante il recupero dei comuni")

        for citta in comuni.json():
            if citta.get("name").upper() == town.upper():
                self.comune_id = citta.get("id", "")
                break
        if self.comune_id is None:
            raise Exception("Comune non trovato")

        indirizzi = api_get_request(
            relative_path="/getIndirizzi.php", params={"idComune": self.comune_id}
        )
        _LOGGER.debug(
            "getIndirizzi.php: %d s - %s - %s",
            indirizzi.elapsed.total_seconds(),
            indirizzi.status_code,
            indirizzi.reason,
        )

        if indirizzi.status_code != 200 or not isinstance(indirizzi.json(), list):
            raise Exception("Errore durante il recupero degli indirizzi")

        for strada in indirizzi.json():
            if strada.get("indirizzo") == street.upper():
                self.inirizzo_id = strada.get("id", "")
                break
        if self.inirizzo_id is None:
            raise Exception("Strada non trovata")

        numeri_civici = api_get_request(
            relative_path="/getNumeriCivici.php",
            params={"idComune": self.comune_id, "idIndirizzo": self.inirizzo_id},
        )
        _LOGGER.debug(
            "getNumeriCivici.php: %d s - %s - %s",
            numeri_civici.elapsed.total_seconds(),
            numeri_civici.status_code,
            numeri_civici.reason,
        )

        if numeri_civici.status_code != 200 or not isinstance(
            numeri_civici.json(), list
        ):
            raise Exception("Errore durante il recupero dei numeri civici")

        for civico in numeri_civici.json():
            if civico.get("numeroCivico") == str(house_number):
                self.civico_id = civico.get("id", "")
                break
        if self.civico_id is None:
            raise Exception("Civico non trovato")

    def fetch(self):
        r = api_get_request(
            relative_path="/getCalendarioPap.php",
            params={
                "idComune": self.comune_id,
                "idIndirizzo": self.inirizzo_id,
                "idCivico": self.civico_id,
                "isBusiness": "0",
                "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "giorniDaMostrare": 31,
            },
        )
        _LOGGER.debug(
            "getCalendarioPap.php: %d s - %s - %s",
            r.elapsed.total_seconds(),
            r.status_code,
            r.reason,
        )

        if r.status_code != 200 or not isinstance(r.json(), dict):
            raise Exception("Errore durante il recupero del calendario")

        calendar = r.json().get("calendario", [])

        entries = []

        for entry in calendar:
            for event in entry.get("conferimenti", []):
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(
                            entry.get("data"), "%Y-%m-%dT%H:%M:%S+00:00"
                        ).date(),
                        t=event.get("macroprodotto").get("descrizione"),
                        icon=ICON_MAP.get(
                            event.get("macroprodotto").get("descrizione")
                        ),
                    )
                )

        return entries


def api_get_request(relative_path, params=None):
    _LOGGER.debug("%s [GET] params: %s", relative_path, params)
    return requests.post(
        url=API_URL,
        data={
            "url": API_URL_BACKEND + relative_path,
            "type": "GET",
            "parameters": json.dumps(params) if params else None,
        },
        headers=HEADERS,
    )
