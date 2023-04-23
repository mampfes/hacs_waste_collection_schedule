import datetime

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
# Include work around for SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error
from waste_collection_schedule.service.SSLError import get_legacy_session

TITLE = "Esch-sur-Alzette"
DESCRIPTION = "Source script for administration.esch.lu, communal website of the city of Esch-sur-Alzette in Luxembourg"
URL = "https://esch.lu"
TEST_CASES = {"Zone A": {"zone": "A"}, "Zone B": {"zone": "B"}}

API_URL = "https://administration.esch.lu/dechets/?street=0&tour="
ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
    "Poubelle ménage": "mdi:trash-can",
    "Papier": "mdi:newspaper",
    "Organique": "mdi:leaf",
    "Verre": "mdi:bottle-wine-outline",
    "Valorlux": "mdi:recycle",
    "Déchets toxiques": "mdi:skull-crossbones",
    "Container ménage": "train-car-container",
}

MONTH_NAMES = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


class Source:
    def __init__(
        self, zone
    ):  # argX correspond to the args dict in the source configuration
        zones = {"A": "1", "B": "2"}
        self._zone = zones[zone]

    def fetch(self):
        s = get_legacy_session()

        # locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8') # set the French locale to import the dates
        params = {
            "street": 0,
            "tour": self._zone,
        }
        r = s.get("https://administration.esch.lu/dechets", params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # Find the table containing the waste collection schedule
        table = soup.find("table", {"id": "garbage-table"})

        entries = []  # List that holds collection schedule
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 3:
                t = cells[1].text.strip()  # Collection type
                if t.startswith("Cartons en vrac"):
                    continue  # Skip the cardboard collection for companies
                if t.startswith("Déchets toxiques"):
                    t = "Déchets toxiques"  # Remove collecting instructions
                date_fr = cells[2].text.strip().split(", ")[1]
                day, month, year = date_fr.split()
                date = datetime.datetime(
                    year=int(year), month=MONTH_NAMES.index(month) + 1, day=int(day)
                ).date()
                entries.append(Collection(date, t, icon=ICON_MAP.get(t)))
        return entries
