import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Entsorgungszweckverband der Gemeinden Liechtensteins (EZV)"
DESCRIPTION = "Source for the waste collection calendar of the EZV, Liechtenstein."
URL = "https://www.ezv.li/abfallentsorgung/abfallkalender/"
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

API_URL = "https://www.ezv.li/abfallentsorgung/abfallkalender"
LABEL_TO_TYPE = {v: k for k, v in WASTE_TYPES.items()}

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
    "en": "Select your municipality from the list and choose a waste type ('kehricht', 'gruenabfuhr', or 'all'). Visit https://www.ezv.li/abfallentsorgung/abfallkalender/ to see the schedule.",
    "de": "Wählen Sie Ihre Gemeinde aus der Liste und den Abfalltyp ('kehricht', 'gruenabfuhr' oder 'all'). Besuchen Sie https://www.ezv.li/abfallentsorgung/abfallkalender/ für den Kalender.",
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
        base = f"{API_URL}/{self._municipality}"
        resp = requests.get(base, timeout=30)
        resp.raise_for_status()
        pages = [resp.text]

        # The calendar page lists the available months in a select box.
        soup = BeautifulSoup(resp.text, "html.parser")
        month_urls = []
        for opt in soup.select("select#pica-filter-month option"):
            value = str(opt.get("value", "")).split("#")[0]
            if value and not opt.get("selected"):
                month_urls.append(f"https://www.ezv.li{value}")
        for url in month_urls:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                pages.append(r.text)

        entries = []
        for html in pages:
            entries.extend(self._parse_page(html))
        return entries

    def _parse_page(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")

        # Year is only given in the caption of the selected month option.
        selected = soup.select_one("select#pica-filter-month option[selected]")
        if selected is None:
            return []
        caption = str(selected.get("data-caption", "")).split()
        try:
            year = int(caption[-1])
            month = MONTHS_DE[caption[0].lower()]
        except (ValueError, IndexError, KeyError):
            return []

        entries = []
        for day_el in soup.select("div.pica-day"):
            day_txt = day_el.select_one(".pica-date-header-day")
            if day_txt is None:
                continue
            try:
                date = datetime.date(year, month, int(day_txt.get_text(strip=True)))
            except ValueError:
                continue
            for name_el in day_el.select(".pica-category-name"):
                label = name_el.get_text(strip=True)
                key = LABEL_TO_TYPE.get(label)
                if key is not None and key not in self._waste_types:
                    continue
                entries.append(Collection(date, label, icon=ICON_MAP.get(label)))
        return entries
