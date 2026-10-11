import datetime
import re

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "FL Abfalltransport AG"
DESCRIPTION = "Source for FL Abfalltransport AG, Liechtenstein."
URL = "https://www.ezv.li/abfallentsorgung/abfallkalender"
BASE_URL = "https://www.ezv.li/abfallentsorgung/abfallkalender"
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
    "en": "Select your municipality from the list and choose a waste type ('kehricht', 'gruenabfuhr', or 'all'). Visit https://www.ezv.li/abfallentsorgung/abfallkalender to see the schedule.",
    "de": "Wählen Sie Ihre Gemeinde aus der Liste und den Abfalltyp ('kehricht', 'gruenabfuhr' oder 'all'). Besuchen Sie https://www.ezv.li/abfallentsorgung/abfallkalender für den Kalender.",
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
        self._labels = {WASTE_TYPES[t] for t in self._waste_types}

    def _parse_waste_types(self, waste_type: str) -> list[str]:
        requested_types = []
        valid_types = list(WASTE_TYPES.keys())
        accepted_types = [*valid_types, "all", "both"]
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
            month_slug = MONTHS_URL[target.month]

            url = f"{BASE_URL}/{self._municipality}/{month_slug}"
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # The day headers carry no year; take it from the selected month option
            year = target.year
            selected = soup.select_one("#pica-filter-month option[selected]")
            if selected is not None:
                match = re.search(r"\b(\d{4})\b", selected.get("data-caption", ""))
                if match:
                    year = int(match.group(1))
            month = target.month

            for day in soup.select(".pica-day"):
                day_tag = day.select_one(".pica-date-header-day")
                if day_tag is None:
                    continue
                try:
                    dt = datetime.date(year, month, int(day_tag.get_text(strip=True)))
                except ValueError:
                    continue

                for name_tag in day.select(".pica-category-name"):
                    label = name_tag.get_text(strip=True)
                    if label not in self._labels:
                        continue
                    entries.append(Collection(dt, label, icon=ICON_MAP.get(label)))

        return entries
