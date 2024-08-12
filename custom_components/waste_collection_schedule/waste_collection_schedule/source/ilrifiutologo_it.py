import logging
import datetime
import requests
import json
from waste_collection_schedule import Collection


TITLE = "Il Rifiutologo"
DESCRIPTION = "Source for ilrifiutologo.it"
URL = "https://ilrifiutologo.it"
COUNTRY = "it"
TEST_CASES = {
    "Test1": {"comune": "Faenza", "indirizzo": "VIA AUGUSTO RIGHI", "civico": "6"}
}

API_URL = "https://www.ilrifiutologo.it/ajax/archivio_ilrifiutologo_ajax.php"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0'}
REQUEST_BASE_URL = "https://webapp-ambiente.gruppohera.it/rifiutologo/rifiutologoweb"
ICON_MAP = {
    "Lattine": "mdi:bottle-soda-classic",
    "Plastica": "mdi:bottle-soda-classic",
    "Indifferenziato": "mdi:trash-can",
    "Vetro": "mdi:glass-fragile",
    "Organico": "mdi:apple",
    "Organico": "mdi:apple",
    "Sfalci e potature": "mdi:leaf",
    "Pannolini/Pannoloni": "mdi:baby-carriage",
    "Carta e cartone": "mdi:newspaper"
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(
            self,
            town: str,
            street: str,
            house_number: int | str
        ):  # argX correspond to the args dict in the source configuration
        self._comune = town
        self._indirizzo = street
        self._civico = house_number

    def fetch(self):

        comuni = api_get_request(relative_path="/getComuni.php")

        for city in comuni.json():
            if city.get('name').upper() == self._comune.upper():
                self._comune = city.get('id')
                break
            if city == comuni.json()[-1]:
                _LOGGER.error("Comune non trovato")
                raise Exception("Comune non trovato")

        indirizzi = api_get_request(
            relative_path="/getIndirizzi.php",
            params={"idComune": self._comune }
        )

        for street in indirizzi.json():
            if street.get('indirizzo') == self._indirizzo.upper():
                self._indirizzo = street.get('id')
                break
            if street == indirizzi.json()[-1]:
                _LOGGER.error("Strada non trovata")
                raise Exception("Strada non trovata")

        numeri_civici = api_get_request(
            relative_path="/getNumeriCivici.php",
            params={"idComune": self._comune, "idIndirizzo": self._indirizzo}
        )

        for number in numeri_civici.json():
            if number.get('numeroCivico') == str(self._civico):
                self._civico = number.get('id')
                break
            if number == numeri_civici.json()[-1]:
                _LOGGER.error("Civico non trovato")
                raise Exception("Civico non trovato")

        r = api_get_request(
            relative_path="/getCalendarioPap.php",
            params={"idComune": self._comune, "idIndirizzo": self._indirizzo, "idCivico": self._civico, "isBusiness": "0", "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "giorniDaMostrare": 31}
        )

        calendar = r.json().get('calendario')

        entries = []

        for entry in calendar:
            for event in entry['conferimenti']:
                entries.append(
                    Collection(
                        date = datetime.datetime.strptime(entry['data'], '%Y-%m-%dT%H:%M:%S+00:00').date(),
                        t = event['macroprodotto']['descrizione'],
                        icon = ICON_MAP.get(event['macroprodotto']['descrizione'], "mdi:trash-can"),
                    )
                )

        return entries
    
def api_get_request(relative_path, params=None):
    return requests.post(
        url=API_URL,
        data={
            "url": REQUEST_BASE_URL + relative_path,
            "type": "GET",
            "parameters": json.dumps(params) if params else None
        },
        headers=HEADERS
    )