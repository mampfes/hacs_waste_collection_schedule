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
    5: "mai",
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
    "Balzers Both": {"municipality": "balzers", "waste_type": "all"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your municipality from the list and choose a waste type ('kehricht', 'gruenabfuhr', or 'all'). Visit https://www.abfalltransport.li/abfallkalender to see the schedule.",
    "de": "Wählen Sie Ihre Gemeinde aus der Liste und den Abfalltyp ('kehricht', 'gruenabfuhr' oder 'all'). Besuchen Sie https://www.abfalltransport.li/abfallkalender für den Kalender.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Municipality name in lower case (e.g. 'balzers', 'vaduz', 'schaan')",
        "waste_type": "Waste type: 'kehricht', 'gruenabfuhr', 'all' (or comma-separated list)",
    },
    "de": {
        "municipality": "Gemeindename in Kleinbuchstaben (z.B. 'balzers', 'vaduz', 'schaan')",
        "waste_type": "Abfalltyp: 'kehricht', 'gruenabfuhr', 'all' (oder komma-separierte Liste)",
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

        if self._municipality not in MUNICIPALITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, MUNICIPALITIES
            )

        self._waste_types = self._parse_waste_types(waste_type)

    def _parse_waste_types(self, waste_type: str) -> list[str]:
        requested_types = []
        valid_types = list(WASTE_TYPES.keys())
        accepted_types = valid_types + ["all", "both"]
        for token in waste_type.lower().replace(";", ",").split(","):
            selected_type = token.strip()
            if not selected_type:
                continue
            if selected_type in ("all", "both"):
                requested_types.extend(valid_types)
                continue
            if selected_type in valid_types:
                requested_types.append(selected_type)
                continue
            raise SourceArgumentNotFoundWithSuggestions(
                "waste_type", selected_type, accepted_types
            )

        if not requested_types:
            raise SourceArgumentNotFoundWithSuggestions(
                "waste_type", waste_type, accepted_types
            )

        deduplicated = []
        for selected_type in requested_types:
            if selected_type not in deduplicated:
                deduplicated.append(selected_type)
        return deduplicated

    def fetch(self) -> list[Collection]:
        entries = []
        today = datetime.date.today()

        for delta_month in range(3):
            target = today.replace(day=1) + relativedelta(months=delta_month)
            month = target.month
            year = target.year

            month_slug = MONTHS_URL[month]
            for selected_type in self._waste_types:
                url = f"https://www.abfalltransport.li/abfallkalender/{self._municipality}/{month_slug}/{selected_type}"
                resp = requests.get(url, timeout=30)
                if resp.status_code != 200 and month_slug == "mai":
                    # Keep compatibility if upstream uses capitalized May slug.
                    fallback_url = f"https://www.abfalltransport.li/abfallkalender/{self._municipality}/Mai/{selected_type}"
                    resp = requests.get(fallback_url, timeout=30)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                year_str = str(year)

                for tag in soup.find_all(string=True):
                    if not ("." in tag and year_str in tag):
                        continue
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
                                    selected_type, selected_type.capitalize()
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
