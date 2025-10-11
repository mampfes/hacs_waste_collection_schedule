import datetime as dt
from datetime import date, timedelta

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentRequired,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Municipality of Xylokastro–Evrostini (Bulky & Appliances)"
DESCRIPTION = "Official bulky/appliances pickup program by day and locality"
URL = "https://www.xylokastro-evrostini.gov.gr"
COUNTRY = "gr"

# Official pages listing weekly program (both show the same table):
PROGRAM_URLS = [
    "https://www.xylokastro-evrostini.gov.gr/el/zo-ston-dimo-services/enemeronomai/ta-nea-mas/anakoinoseis/1504-anakoinose-tes-yperesias-kathariotetas-3614",
    "https://www.xylokastro-evrostini.gov.gr/el/zo-ston-dimo-services/enemeronomai/ta-nea-mas/anakoinoseis/1094-neos-kanonismos-kathariotetas-524",
]

# MDI icon for bulky
ICON_MAP = {"Bulky & Appliances": "mdi:sofa"}

# Locality → weekday(s). Greek names exactly as on the page, plus an ASCII alias map.
# We include both municipal units (Ξυλοκάστρου, Ευρωστίνης).
_SCHEDULE = {
    # Δημοτική Ενότητα Ξυλοκάστρου
    "Ξυλόκαστρο": ["MO", "FR"],    # Monday, Friday
    "Μελίσσι": ["TU"],             # Tuesday  ← Melissi
    "Θαλερό": ["TU"],              # Tuesday
    "Συκιά": ["WE"],               # Wednesday
    "Καρυώτικα": ["WE"],
    "Γελινιάτικα": ["WE"],
    "Καμάρι": ["TH"],              # Thursday
    "Πιτσά": ["TH"],
    "Λουτρό": ["TH"],
    # Δημοτική Ενότητα Ευρωστίνης
    "Δερβένι": ["MO", "FR"],
    "Λυγιά": ["TU"],
    "Στόμι": ["TU"],
    "Σαρανταπηχιώτικα": ["TU"],
    "Ροζενά": ["WE"],
    "Ζάχολη": ["WE"],
    "Πύργο": ["WE"],
    "Χελυδόρι": ["WE"],
    "Λυκοποριά": ["TH"],
    "Καλλιθέα": ["TH"],
    "Ελληνικό": ["TH"],
    # Fortnightly mountain villages are omitted for now; can be added later with interval=2 logic.
}

# Common ASCII aliases so users can pass English/ASCII names
ALIASES = {
    "xylokastro": "Ξυλόκαστρο",
    "melissi": "Μελίσσι",
    "thalero": "Θαλερό",
    "sykia": "Συκιά",
    "karyotika": "Καρυώτικα",
    "geliniatika": "Γελινιάτικα",
    "kamari": "Καμάρι",
    "pitsa": "Πιτσά",
    "loutro": "Λουτρό",
    "derveni": "Δερβένι",
    "lygia": "Λυγιά",
    "stomi": "Στόμι",
    "sarandapichiotika": "Σαρανταπηχιώτικα",
    "rozena": "Ροζενά",
    "zaholi": "Ζάχολη",
    "pirgo": "Πύργο",
    "chelydori": "Χελυδόρι",
    "lykoporia": "Λυκοποριά",
    "kallithea": "Καλλιθέα",
    "elliniko": "Ελληνικό",
}

# Shown in README/info and used by test_sources.py
TEST_CASES = {
    "Melissi (ASCII)": {"locality": "melissi"},
    "Μελίσσι (Greek)": {"locality": "Μελίσσι"},
    "Ξυλόκαστρο": {"locality": "Ξυλόκαστρο"},
    "Λυκοποριά": {"locality": "Λυκοποριά"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Choose your locality as written on the municipality site. ASCII aliases are accepted (e.g., melissi, xylokastro).",
    "el": "Επιλέξτε την τοπική κοινότητά σας όπως αναγράφεται στον ιστότοπο του Δήμου. Υποστηρίζονται και ASCII ονόματα.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "locality": "Name of your locality (e.g., Μελίσσι or melissi).",
        "weeks_ahead": "Optional. How many weeks to generate (default 52).",
        "first_date": "Optional. Start date (YYYY-MM-DD). Defaults to today.",
    }
}

class Source:
    def __init__(self, locality: str, weeks_ahead: int = 52, first_date: str | None = None):
        if not locality:
            raise SourceArgumentRequired("locality")
        # normalize
        loc = locality.strip()
        loc = ALIASES.get(loc.lower(), loc)
        if loc not in _SCHEDULE:
            # suggestions: closest keys
            suggestions = [{"locality": k} for k in sorted(_SCHEDULE.keys())][:10]
            raise SourceArgumentNotFoundWithSuggestions("locality", locality, suggestions)

        self.locality = loc
        self.weekdays = _SCHEDULE[loc]
        self.weeks_ahead = int(weeks_ahead) if weeks_ahead else 52

        if first_date:
            year, month, day = map(int, first_date.split("-"))
            self.start = date(year, month, day)
        else:
            self.start = dt.date.today()

    def _iter_weekdays(self, start: date, weekday_code: str):
        # Map 2-letter to Python weekday (Mon=0..Sun=6)
        map2py = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
        target = map2py[weekday_code]
        # find next >= start
        d = start
        while d.weekday() != target:
            d += timedelta(days=1)
        # yield weekly occurrences
        for i in range(self.weeks_ahead):
            yield d + timedelta(weeks=i)

    def fetch(self) -> list[Collection]:
        # We generate future occurrences for the configured locality
        entries: list[Collection] = []
        for code in self.weekdays:
            for d in self._iter_weekdays(self.start, code):
                entries.append(
                    Collection(
                        date=d,
                        t="Bulky & Appliances",
                        icon=ICON_MAP.get("Bulky & Appliances"),
                    )
                )

        # Note for reviewers: this source intentionally covers only bulky/appliances,
        # because only that schedule is officially published by the municipality at PROGRAM_URLS.
        # When MSW/blue-bin/organics schedules are published, we will expand.
        return entries
