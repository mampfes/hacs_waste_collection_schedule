from datetime import date as datetime_date
from datetime import datetime as datetime_datetime
from datetime import timedelta
from typing import Dict, List

import requests
from icalendar import Calendar
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "RITL"
DESCRIPTION = (
    "Source for Régie intermunicipale des Trois-Lacs (RITL) waste collection schedule."
)
URL = "https://ritl.ca/"
COUNTRY = "ca"

# Declare codeowners (the user can customize this)
SOURCE_CODEOWNERS = ["@Jean-PascalComeau"]

# List of all supported municipalities and their sectors
MUNICIPALITIES: Dict[str, Dict[str, List[int]]] = {
    "Ivry-sur-le-Lac": {
        "all": [29, 30, 31],
    },
    "Lac-Supérieur": {
        "Secteur 1": [20, 21, 22],
        "Secteur 2": [39, 40, 41],
    },
    "Lantier": {
        "all": [23, 24, 25],
    },
    "Montcalm": {
        "Secteur 1": [69, 70, 71],
    },
    "Mont-Blanc": {
        "Secteur Est": [15, 16, 38],
        "Secteur Ouest": [35, 36, 37],
    },
    "Sainte-Agathe-des-Monts": {
        "Secteur Centre-ville": [26, 27, 28],
        "Secteur Nord": [42, 43, 44],
        "Secteur Sud / Fatima": [45, 46, 47],
    },
    "Sainte-Lucie-des-Laurentides": {
        "all": [12, 13, 14],
    },
    "Val-des-Lacs": {
        "all": [32, 33, 34],
    },
    "Val-David": {
        "Secteur 1": [53, 56, 76],
        "Secteur 2": [54, 57, 59, 60],
        "Secteur 3": [55, 58, 77],
    },
    "Val-Morin": {
        "Val-Morin Est": [65, 66, 67],
        "Val-Morin Ouest": [61, 62, 63],
    },
}

TEST_CASES = {
    "Lac-Supérieur Secteur 1": {
        "municipality": "Lac-Supérieur",
        "sector": "Secteur 1",
    },
    "Lac-Supérieur Secteur 2": {
        "municipality": "Lac-Supérieur",
        "sector": "Secteur 2",
    },
    "Ivry-sur-le-Lac": {
        "municipality": "Ivry-sur-le-Lac",
    },
    "Val-David Secteur 2": {
        "municipality": "Val-David",
        "sector": "Secteur 2",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Name of the municipality (e.g., Lac-Supérieur, Lantier, Sainte-Agathe-des-Monts...)",
        "sector": "Sector name (only required for municipalities with sectors)",
    },
    "fr": {
        "municipality": "Nom de la municipalité (ex: Lac-Supérieur, Lantier, Sainte-Agathe-des-Monts...)",
        "sector": "Nom du secteur (requis uniquement pour les municipalités avec secteurs)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "sector": "Sector",
    },
    "fr": {
        "municipality": "Municipalité",
        "sector": "Secteur",
    },
}

ICON_MAP = {
    "Déchets": Icons.GENERAL_WASTE,
    "Recyclage": Icons.RECYCLING,
    "Compost": Icons.ORGANIC,
}

SECTOR_SYNONYMS = {
    "1": "secteur-1",
    "a": "secteur-1",
    "secteur-a": "secteur-1",
    "2": "secteur-2",
    "b": "secteur-2",
    "secteur-b": "secteur-2",
    "3": "secteur-3",
    "est": "secteur-est",
    "ouest": "secteur-ouest",
    "centre-ville": "secteur-centre-ville",
    "nord": "secteur-nord",
    "sud-fatima": "secteur-sud-/-fatima",
    "sud": "secteur-sud-/-fatima",
    "fatima": "secteur-sud-/-fatima",
    "secteur-sud-fatima": "secteur-sud-/-fatima",
    "est-val-morin": "val-morin-est",
    "ouest-val-morin": "val-morin-ouest",
}


def normalize(s: str) -> str:
    s = s.strip().lower()
    for a, b in [
        ("é", "e"),
        ("è", "e"),
        ("ê", "e"),
        ("ë", "e"),
        ("à", "a"),
        ("â", "a"),
        ("ô", "o"),
        ("û", "u"),
        ("ù", "u"),
        ("ï", "i"),
        ("î", "i"),
        ("ç", "c"),
    ]:
        s = s.replace(a, b)
    return s.replace(" ", "-").replace("_", "-")


MUNICIPALITIES_NORMALIZED = {}
for m_name, sectors in MUNICIPALITIES.items():
    norm_m = normalize(m_name)
    norm_sectors = {}
    for s_name, ids in sectors.items():
        norm_s = normalize(s_name)
        norm_sectors[norm_s] = (s_name, ids)
    MUNICIPALITIES_NORMALIZED[norm_m] = (m_name, norm_sectors)


class Source:
    def __init__(self, municipality: str, sector: str | None = None):
        norm_m = normalize(municipality)
        if norm_m not in MUNICIPALITIES_NORMALIZED:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", municipality, MUNICIPALITIES.keys()
            )

        _m_display, norm_sectors = MUNICIPALITIES_NORMALIZED[norm_m]

        if len(norm_sectors) == 1 and "all" in norm_sectors:
            chosen_sector_norm = "all"
        else:
            if not sector:
                raise SourceArgumentNotFoundWithSuggestions(
                    "sector",
                    sector,
                    [name for name, _ in norm_sectors.values()],
                )

            norm_s = normalize(str(sector))
            if norm_s in norm_sectors:
                chosen_sector_norm = norm_s
            else:
                resolved = SECTOR_SYNONYMS.get(norm_s)
                if resolved in norm_sectors:
                    chosen_sector_norm = resolved
                elif norm_m == "val-morin":
                    if norm_s in ("est", "val-morin-est"):
                        chosen_sector_norm = "val-morin-est"
                    elif norm_s in ("ouest", "val-morin-ouest"):
                        chosen_sector_norm = "val-morin-ouest"
                    else:
                        chosen_sector_norm = None
                elif norm_m == "mont-blanc":
                    if norm_s == "est":
                        chosen_sector_norm = "secteur-est"
                    elif norm_s == "ouest":
                        chosen_sector_norm = "secteur-ouest"
                    else:
                        chosen_sector_norm = None
                else:
                    chosen_sector_norm = None

            if not chosen_sector_norm or chosen_sector_norm not in norm_sectors:
                raise SourceArgumentNotFoundWithSuggestions(
                    "sector",
                    sector,
                    [name for name, _ in norm_sectors.values()],
                )

        _, self._cat_ids = norm_sectors[chosen_sector_norm]

    def fetch(self) -> List[Collection]:
        cat_ids_str = ",".join(str(cid) for cid in self._cat_ids)
        params = {
            "plugin": "all-in-one-event-calendar",
            "controller": "ai1ec_exporter_controller",
            "action": "export_events",
            "ai1ec_cat_ids": cat_ids_str,
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://ritl.ca/", params=params, headers=headers, timeout=30)
        r.raise_for_status()

        cal = Calendar.from_ical(r.text)

        today = datetime_date.today()
        start_date = today
        end_date = today + timedelta(days=365)

        entries = []

        for component in cal.walk():
            if component.name == "VEVENT":
                summary = component.get("summary")
                categories = component.get("categories")

                # Combine categories and summary to identify waste type
                check_strings = []
                if summary:
                    check_strings.append(str(summary))
                if categories:
                    if hasattr(categories, "cats"):
                        check_strings.extend(str(c) for c in categories.cats)
                    elif isinstance(categories, list):
                        check_strings.extend(str(c) for c in categories)
                    else:
                        check_strings.append(str(categories))

                check_text = " ".join(check_strings).lower()

                if "compost" in check_text or "organique" in check_text:
                    t = "Compost"
                elif any(
                    w in check_text
                    for w in [
                        "récupération",
                        "recuperation",
                        "recyclage",
                        "recup",
                        "bleu",
                    ]
                ):
                    t = "Recyclage"
                elif any(w in check_text for w in ["déchets", "dechets", "ordures"]):
                    t = "Déchets"
                else:
                    t = str(summary) if summary else "Unknown"

                # Extract dates
                dates = []

                # DTSTART
                dtstart_prop = component.get("dtstart")
                if dtstart_prop:
                    dt = dtstart_prop.dt
                    if isinstance(dt, datetime_datetime):
                        dates.append(dt.date())
                    elif isinstance(dt, datetime_date):
                        dates.append(dt)

                # RDATEs
                rdate_prop = component.get("rdate")
                if rdate_prop:
                    if not isinstance(rdate_prop, list):
                        rdate_prop = [rdate_prop]
                    for r in rdate_prop:
                        if hasattr(r, "dts"):
                            for dt_item in r.dts:
                                dt = dt_item.dt
                                if isinstance(dt, datetime_datetime):
                                    dates.append(dt.date())
                                elif isinstance(dt, datetime_date):
                                    dates.append(dt)
                        elif hasattr(r, "dt"):
                            dt = r.dt
                            if isinstance(dt, datetime_datetime):
                                dates.append(dt.date())
                            elif isinstance(dt, datetime_date):
                                dates.append(dt)

                # Filter and add collections
                icon = ICON_MAP.get(t)
                seen_dates = set()
                for d in dates:
                    if start_date <= d <= end_date and d not in seen_dates:
                        seen_dates.add(d)
                        entries.append(Collection(date=d, t=t, icon=icon))

        return entries
