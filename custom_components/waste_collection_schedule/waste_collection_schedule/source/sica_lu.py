import requests
import datetime
from waste_collection_schedule import Collection

TITLE = "SICA"
DESCRIPTION = "Source script for sica.lu served municipalities"
URL = "https://sica.lu"
TEST_CASES = {
    "Bertrange": {"municipality": "Bertrange"},
    "Capellen": {"municipality": "Capellen"},
    "Garnich": {"municipality": "Garnich"},
    "Holzem": {"municipality": "Holzem"},
    "Kehlen": {"municipality": "Kehlen"},
    "Koerich": {"municipality": "Koerich"},
    "Kopstal": {"municipality": "Kopstal"},
    "Mamer": {"municipality": "Mamer"},
    "Septfontaines": {"municipality": "Septfontaines"},
    "Steinfort": {"municipality": "Steinfort"},
}

API_URL = f"http://sicaapp.lu/wp-json/wp/v2"
ICON_MAP = {
    "Residual waste": "mdi:trash-can",
    "Valorlux packaging": "mdi:recycle",
    "Organic waste": "mdi:leaf",
    "Glass": "mdi:bottle-wine-outline",
    "Paper - Cartons": "mdi:newspaper",
    "Scrap and electrical appliances": "mdi:washing-machine",
    "Clothing and Shoes": "mdi:tshirt-crew",
    "Trees, shrubs and hedges": "mdi:tree",
}

MUNICIPALITIES = {
    "Bertrange": 28,
    "Capellen": 138,
    "Garnich": 29,
    "Holzem": 139,
    "Kehlen": 30,
    "Koerich": 31,
    "Kopstal": 24,
    "Mamer": 137,
    "Septfontaines": 26,
    "Steinfort": 27,
}


class Source:
    def __init__(self, municipality):
        # https://sicaapp.lu/wp-json/wp/v2/locations/

        self._municipality = MUNICIPALITIES.get(municipality)

    def fetch(self):
        headers = {"User-Agent": "SicaAPP", "Accept": "application/json"}
        year = datetime.datetime.now().year
        url = f"{API_URL}/calendaryear/{self._municipality}/{year}"

        # Retrieve specified municipality from API as JSON
        r = requests.get(url, headers)
        if r.status_code != 200:
            r.raise_for_status()
        try:
            data = r.json()
        except ValueError as e:
            raise ValueError(f"Error decoding JSON from SICA API: {e} - {r.text}")

        # Extract collection dates
        entries = []
        for month in data:
            for day in month["schedule"]:
                pickup_date = datetime.datetime.strptime(day["date"], "%Y%m%d").date()
                for pickup in day["pickupTypes"]:
                    entries.append(
                        Collection(
                            date=pickup_date,
                            t=pickup["name"],
                            icon=ICON_MAP.get(pickup["name"]),
                            picture=pickup["img"],
                        )
                    )

        return entries
