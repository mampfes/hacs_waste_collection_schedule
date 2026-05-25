import datetime
import json
import requests
from waste_collection_schedule import Collection

TITLE = "Odvoz Odpadu"
DESCRIPTION = "Zdroj pre harmonogram odvozu odpadu z portálu odvoz-odpadu.eu."
URL = "https://odvoz-odpadu.eu"
COUNTRY = "sk"

# TEST_CASES slúži pre automatický test na GitHube, aby overil funkčnosť obce Dolná Ves
TEST_CASES = {
    "Dolná Ves": {"city": "dolna_ves"}
}

API_URL = "https://odvoz-odpadu.eu/api/v1/get-by-municipality"

class Source:
    def __init__(self, city):
        self._city = city

    def fetch(self):
        payload = {"municipality_slug": self._city}
        r = requests.post(API_URL, json=payload)
        r.raise_for_status()
        
        data = r.json()
        entries = []
        
        # Spracovanie prijatých dát o odvoze odpadu
        for date_str, waste_types in data.items():
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            for waste in waste_types:
                entries.append(Collection(date=date, t=waste["title"]))
                
        return entries
