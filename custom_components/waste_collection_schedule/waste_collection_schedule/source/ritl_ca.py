import logging
from typing import Dict, List

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "RITL"
DESCRIPTION = "Source for Régie intermunicipale des Trois-Lacs (RITL) waste collection schedule."
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
        self._ics = ICS()

        norm_m = normalize(municipality)
        if norm_m not in MUNICIPALITIES_NORMALIZED:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", municipality, MUNICIPALITIES.keys()
            )

        m_display, norm_sectors = MUNICIPALITIES_NORMALIZED[norm_m]

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
        r = requests.get("https://ritl.ca/", params=params, headers=headers)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for date, summary in dates:
            summary_lower = summary.lower()
            if "compost" in summary_lower or "organique" in summary_lower:
                t = "Compost"
            elif (
                "récupération" in summary_lower
                or "recuperation" in summary_lower
                or "recyclage" in summary_lower
                or "recup" in summary_lower
                or "bleu" in summary_lower
            ):
                t = "Recyclage"
            elif (
                "déchets" in summary_lower
                or "dechets" in summary_lower
                or "ordures" in summary_lower
            ):
                t = "Déchets"
            else:
                t = summary

            icon = ICON_MAP.get(t)
            entries.append(Collection(date=date, t=t, icon=icon))

        return entries
