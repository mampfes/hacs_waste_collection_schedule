# import datetime
from datetime import date
from waste_collection_schedule import Collection
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, rrule, weekday, WEEKLY
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import dateparser
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Communauté de Communes de Montesquieu"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for cc-montesquieu.fr"  # Describe your source
URL = "https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets"  # Insert url to service homepage. URL will show up in README.md and info.md
COUNTRY = "fr"

COMMUNES = [
    "Ayguemorte-les-Graves",
    "Beautiran",
    "Cabanac-et-Villagrains",
    "Cadaujac",
    "Castres-Gironde",
    "Isle Saint-Georges",
    "La Brède",
    "Léognan",
    "Martillac",
    "Saint-Médard-d’Eyrans",
    "Saint-Morillon",
    "Saint-Selve",
    "Saucats",
]

TEST_CASES = {commune: {"commune": commune} for commune in COMMUNES}

# API_URL = "https://abc.com/search/"
ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
    "Bac d'ordures ménagères": "mdi:trash-can",
    "Bac jaune": "mdi:recycle",
    "Déchets verts": "mdi:leaf",
    "Encombrants": "mdi:dump-truck",
}

WEEKDAY_MAP = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}

BIN_TYPE_MAP = {"Bac d'ordures ménagères": "ordures", "Bac jaune": "recyclage"}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
    "de": "WIE MAN DIE ARGUMENTE ERHÄLT",
    "it": "COME OTTENERE GLI ARGOMENTI",
}


PARAM_DESCRIPTIONS = {
    "en": {
        "commune": "city of Montesquieu's community : " + ", ".join(COMMUNES),
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "commune": "City",
    },
    "de": {
        "commune": "Stadt",
    },
}
#### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, commune: str):
        self.commune = commune

        if self.commune not in COMMUNES:
            raise SourceArgumentNotFoundWithSuggestions(
                "Commune", self.commune, COMMUNES.keys()
            )

    def fetch(self) -> list[Collection]:

        global_planning = self.get_planning_table()
        city_planning = global_planning[self.commune]

        entries = []  # List that holds collection schedule

        for bin_type in city_planning.keys():
            french_day = city_planning[bin_type]

            collection_day = WEEKDAY_MAP[french_day.strip().lower()]

            for dt in rrule(
                freq=WEEKLY,
                dtstart=date.today(),
                count=20,
                byweekday=collection_day,
            ):
                entries.append(
                    Collection(
                        date=dt.date(),  # Collection date
                        t=bin_type,  # Collection type
                        icon=ICON_MAP.get(bin_type),  # Collection icon
                    )
                )

        global_planning = self.get_planning_table_dechets_verts_et_encombrants()
        city_planning = global_planning[self.commune]

        for bin_type in city_planning.keys():
            for dt in city_planning[bin_type]:
                entries.append(
                    Collection(
                        date=dt,  # Collection date
                        t=bin_type,  # Collection type
                        icon=ICON_MAP.get(bin_type),  # Collection icon
                    )
                )

        return entries

    def get_planning_table(self):
        s = requests.Session()
        response = s.get(URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        planning = {}
        for table in tables:
            if str(table).__contains__("Bac d'ordures ménagères"):
                table_rows = table.find_all("tr")
                th = table_rows[0].find_all("th")
                for t in table_rows[1:]:
                    td = t.find_all("td")
                    ville = td[0].text.strip()
                    planning[ville] = {
                        th[1].text: td[1].text.strip(),
                        th[2].text: td[2].text.strip(),
                    }
        return planning

    def get_planning_table_dechets_verts_et_encombrants(self):
        s = requests.Session()
        response = s.get(URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        planning = {}
        tables = soup.find_all("div", class_="block-openclose skin-openclose")
        for t in tables:
            dechet = t.find("h3", class_="title")
            table_rows = t.find_all("tr")
            for row in table_rows:
                td = row.find_all("td")
                if td:
                    villes = [
                        ville.text.strip() for ville in td[0].find_all(string=True)
                    ]
                    parsed_dates = [
                        dateparser.parse(date.text.strip(), languages=["fr"]).date()
                        for date in td[1].find_all("p")
                    ]
                    for ville in villes:
                        try:
                            planning[ville][dechet.text.strip()] = parsed_dates
                        except KeyError:
                            planning[ville] = dict()
                            planning[ville][dechet.text.strip()] = parsed_dates

        return planning
