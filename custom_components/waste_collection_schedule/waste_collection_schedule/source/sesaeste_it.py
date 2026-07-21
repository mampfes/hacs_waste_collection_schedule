import datetime, requests, logging
from io import BytesIO
from bs4 import BeautifulSoup
from custom_components.waste_collection_schedule.waste_collection_schedule.exceptions import SourceArgAmbiguousWithSuggestions, SourceArgumentNotFound
from waste_collection_schedule import Collection, Icons

TITLE = "S.E.S.A."
DESCRIPTION = "Source script for sesaeste.it"
BASE_URL = "https://sesaeste.it"
URL = BASE_URL
API_URL = BASE_URL + "/proc_cerca_comune/"

TEST_CASES = {
    "Legnaro": {"user_municipality": "Legnaro"},
    "Solesino": {"user_municipality": "Solesino"},
    "TestName3": {"user_municipality": "Polverara"}
}

ICON_MAP = {
    "PLASTICA E LATTINE": Icons.PLASTIC_PACKAGING, # TODO: add an mdi icon for plastic+metal? Probably useful for other sources too.
    "UMIDO": Icons.BIO_KITCHEN,
    "SECCO": Icons.GENERAL_WASTE,
    "CARTA": Icons.PAPER,
    "VETRO": Icons.GLASS,
    "VERDE": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "user_municipality": "Municipality",
    },
    "it": {
        "user_municipality": "Comune",
    },
}


#### End of arguments affecting the configuration GUI ####

logger = logging.getLogger(__name__)

class Source:
    def __init__(self, user_municipality: str):
        self.user_municipality = user_municipality

    def _fetch_municipality_id(self) -> str:
        html_cercacomune = BeautifulSoup(requests.get(API_URL).text)
        select = html_cercacomune.find(id="RifComune")
        candidates: list[tuple[str, str]] = []

        if select is None:
            raise ValueError(f"The S.E.S.A. landing webpage has an unexpected format and the list of municipalities could not be found.")
    
        for opt in select.find_all('option'):
            if opt.string.lower() == self.user_municipality.lower():
                candidates = [(opt.get('value'), opt.string)]
                break
            if self.user_municipality.lower() in opt.string.lower():
                candidates.append((opt.get('value'), opt.string))
        
        if len(candidates) == 0:
            raise SourceArgumentNotFound("user_municipality", self.user_municipality)
        if len(candidates) > 1:
            raise SourceArgAmbiguousWithSuggestions("user_municipality", self.user_municipality, [m for _, m in candidates])
        
        return candidates[0][0]

    
    def _fetch_pdf_calendar(self):
        mun_id = self._fetch_municipality_id()

        html_calendario = BeautifulSoup(
            requests.post(API_URL, {
                'RifComune': mun_id,
                'showheader': False
            }).text
        )
        
        a = html_calendario.find('a', title='Scarica il calendario')
        if a is None:
            raise ValueError(f"The S.E.S.A. municipality webpage has an unexpected format and the PDF schedule link could not be found.")
        
        pdf_url = BASE_URL + a.get('href')
        req = requests.get(pdf_url, stream=True)
        req.raise_for_status()
        pdf_data = BytesIO(req.content)

        return pdf_data


    def fetch(self) -> list[Collection]:
        pdf_data = self._fetch_pdf_calendar()
        logger.info(f"Downloaded {pdf_data} bytes")

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details
        if ERROR_CONDITION:
            raise Exception("YOUR ERROR MESSAGE HERE") # DO NOT JUST return []

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date = datetime.datetime(2020, 4, 11),  # Collection date
                t = "Waste Type",  # Collection type
                icon = ICON_MAP.get("Waste Type"),  # Collection icon
            )
        )

        return entries