import json
import re
import requests
from datetime import datetime
from waste_collection_schedule import Collection  # noqa: F401

TITLE = "PreZero Bielsko-Biała"
DESCRIPTION = "Źródło dla harmonogramu odbioru odpadów PreZero w Bielsko-Białej"
URL = "https://prezero-bielsko.pl/"
COUNTRY = "pl"

API_URL = "https://prezero-bielsko.pl/harmonogramy/index.php"

WASTE_TYPE_MAP = {
    "kuchenne": "Bio",
    "resztkowe": "Pozostałości po segregowaniu",
    "makulatura": "Papier",
    "szklo": "Szkło",
    "mix": "Metale i tworzywa sztuczne",
    "zielone": "Zielone",
    "gabaryty": "Gabaryty"
}

class Source:
    def __init__(self, q: str, rok: int):
        self._q = q
        self._rok = rok

    def fetch(self):

        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-requested-with": "XMLHttpRequest",
        }
        data = {
            "option": "com_sita",
            "view": "daty",
            "q": self._q,
            "rok": str(self._rok),
        }

        response = requests.post(API_URL, headers=headers, data=data)
        response.raise_for_status()

        # Elimination of "eval" nesting
        match = re.search(r'eval\((.*)\)', response.text)
        if not match:
            raise ValueError("Odpowiedź serwera nie jest zgodna z oczekiwanym formatem.")

        json_data = match.group(1).strip()

        # Removing trailing commas from JSON
        json_data = re.sub(r',\s*([\]}])', r'\1', json_data)

        data = json.loads(json_data)

        entries = []
        for item in data["dane"]:
            date_str = f"{self._rok}-{item['data_m']}-{item['data_d']}"
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            waste_type = WASTE_TYPE_MAP.get(item["rodzaj"], "unknown")

            entries.append(Collection(date, waste_type))

        return entries