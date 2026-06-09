import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "FL Abfalltransport AG"
DESCRIPTION = "Source for FL Abfalltransport AG, Liechtenstein."
URL = "https://www.abfalltransport.li"
COUNTRY = "li"

MUNICIPALITIES = [
    "balzers",
    "triesen",
    "triesenberg",
    "vaduz",
    "schaan",
    "planken",
    "gamprin-bendern",
    "ruggell",
    "mauren-schaanwald",
    "eschen-nendeln",
    "schellenberg",
]

WASTE_TYPES = {
    "kehricht": "Kehricht",
    "gruenabfuhr": "Grünabfuhr",
}

# Month number → URL slug (as expected by the website)
MONTHS_URL = {
    1: "januar",
    2: "februar",
    3: "maerz",
    4: "april",
    5: "Mai",
    6: "juni",
    7: "juli",
    8: "august",
    9: "september",
    10: "oktober",
    11: "november",
    12: "dezember",
}

# German month name in HTML → month number
MONTHS_DE = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

ICON_MAP = {
    "Kehricht": Icons.GENERAL_WASTE,
    "Grünabfuhr": Icons.GARDEN,
}

TEST_CASES = {
    "Balzers Kehricht": {"municipality": "balzers", "waste_type": "kehricht"},
    "Vaduz Grünabfuhr": {"municipality": "vaduz", "waste_type": "gruenabfuhr"},
    "Schaan Kehricht": {"municipality": "schaan", "waste_type": "kehricht"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your municipality from the list and choose a waste type ('kehricht' for household waste or 'gruenabfuhr' for green waste). Visit https://www.abfalltransport.li/abfallkalender to see the schedule.",
    "de": "Wählen Sie Ihre Gemeinde aus der Liste und den Abfalltyp ('kehricht' für Kehricht oder 'gruenabfuhr' für Grünabfuhr). Besuchen Sie https://www.abfalltransport.li/abfallkalender für den Kalender.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Municipality name in lower case (e.g. 'balzers', 'vaduz', 'schaan')",
        "waste_type": "Waste type: 'kehricht' (household waste) or 'gruenabfuhr' (green waste)",
    },
    "de": {
        "municipality": "Gemeindename in Kleinbuchstaben (z.B. 'balzers', 'vaduz', 'schaan')",
        "waste_type": "Abfalltyp: 'kehricht' (Kehricht) oder 'gruenabfuhr' (Grünabfuhr)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "waste_type": "Waste type",
    },
    "de": {
        "municipality": "Gemeinde",
        "waste_type": "Abfalltyp",
    },
}


def EXTRA_INFO():
    return [
        {
            "title": m.replace("-", " ").title(),
            "default_params": {"municipality": m},
        }
        for m in MUNICIPALITIES
    ]


class Source:
    def __init__(self, municipality: str, waste_type: str = "kehricht"):
        self._municipality = municipality.lower().strip()
        self._waste_type = waste_type.lower().strip()

        if self._municipality not in MUNICIPALITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, MUNICIPALITIES
            )

        if self._waste_type not in WASTE_TYPES:
            raise SourceArgumentNotFoundWithSuggestions(
                "waste_type", self._waste_type, list(WASTE_TYPES.keys())
            )

    def fetch(self) -> list[Collection]:
        entries = []
        today = datetime.date.today()

        for delta_month in range(3):
            target = today.replace(day=1) + relativedelta(months=delta_month)
            month = target.month
            year = target.year

            month_slug = MONTHS_URL[month]
            url = f"https://www.abfalltransport.li/abfallkalender/{self._municipality}/{month_slug}/{self._waste_type}"
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for tag in soup.find_all(
                string=lambda t: t and "." in t and str(year) in t
            ):
                text = tag.strip()
                parts = text.split()
                if len(parts) == 3:
                    try:
                        day = int(parts[0].replace(".", ""))
                        mon = MONTHS_DE.get(parts[1].lower())
                        yr = int(parts[2])
                        if mon:
                            dt = datetime.date(yr, mon, day)
                            label = WASTE_TYPES.get(
                                self._waste_type, self._waste_type.capitalize()
                            )
                            entries.append(
                                Collection(
                                    dt,
                                    label,
                                    icon=ICON_MAP.get(label),
                                )
                            )
                    except (ValueError, KeyError):
                        pass

        return entries
