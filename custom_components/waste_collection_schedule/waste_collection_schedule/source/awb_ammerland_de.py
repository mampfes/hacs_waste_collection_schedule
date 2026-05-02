import datetime
import json
from typing import Optional

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "AWB Ammerland"
DESCRIPTION = "Source for AWB Ammerland (Abfallwirtschaftsbetrieb Landkreis Ammerland)."
URL = "https://www.awb-ammerland.de"

TEST_CASES = {
    "Edewecht - Schepser Damm": {
        "city": "Edewecht",
        "street": "Schepser Damm",
    },
    "Westerstede - Ammerlandallee nördlich A28": {
        "city": "Westerstede",
        "street": "Ammerlandallee",
        "street_section": "nördl.d. A 28",
    },
    "Wiefelstede - Ahlerskamp (4-wöchentl. Restabfall)": {
        "city": "Wiefelstede",
        "street": "Ahlerskamp",
        "four_weekly_rest": True,
    },
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Gelber Sack": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Ast- und Strauchwerk": "mdi:tree",
    "Problemstoffe": "mdi:biohazard",
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "street_section": "Straßenabschnitt",
        "four_weekly_rest": "4-wöchentlicher Restabfallrhythmus",
    },
    "en": {
        "city": "City",
        "street": "Street",
        "street_section": "Street section",
        "four_weekly_rest": "4-weekly residual waste collection",
    },
}

PARAM_DESCRIPTIONS = {
    "de": {
        "street_section": "Nur erforderlich, wenn die Straße in mehrere Abschnitte aufgeteilt ist (z.B. 'nördl.d. A 28').",
        "four_weekly_rest": "Aktivieren, wenn ein 4-wöchentlicher Abfuhrrythmus für die Restabfalltonne beantragt wurde.",
    },
    "en": {
        "street_section": "Only required if the street is divided into sections (e.g. 'nördl.d. A 28').",
        "four_weekly_rest": "Enable if a 4-weekly collection interval for residual waste has been requested.",
    },
}

# Firebase Storage endpoint (app version 2.21+, path and/7/)
API_URL = "https://firebasestorage.googleapis.com/v0/b/abfall-ammerland.appspot.com/o/and%2F7%2Fawbapp.json?alt=media"

# Waste type bitmask constants (from GUtil.java)
_MART_RES = 1  # Restabfall
_MART_BIO = 2  # Bioabfall
_MART_WER = 4  # Gelber Sack
_MART_PAP = 8  # Papier
_MART_AST = 16  # Sperrmüll / Ast- und Strauchwerk
_MART_PRO = 32  # Problemstoffe

# Map of city name → ortid (matches Ort table in the app)
_CITY_MAP = {
    "Apen": 1,
    "Bad Zwischenahn": 2,
    "Edewecht": 3,
    "Rastede": 4,
    "Westerstede": 5,
    "Wiefelstede": 6,
}


class Source:
    def __init__(
        self,
        city: str,
        street: str,
        street_section: Optional[str] = None,
        four_weekly_rest: bool = False,
    ):
        self._city = city
        self._street = street
        self._street_section = street_section
        self._four_weekly_rest = four_weekly_rest

    def fetch(self) -> list[Collection]:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()

        # The response is 12 JSON arrays joined by "##"
        blocks = response.text.split("##")
        parts = [json.loads(b) for b in blocks if b.strip()]

        # part indices (0-based):
        # 0=Str (streets), 1=Strgr (street sections), 2=Astgr,
        # 3=Strdat (schedule), 4=Astdat (ast mapping),
        # 5=Kal1 (daily reference), 6=Kal2 (Sperrmüll/Ast),
        # 7=Kal3 (Problemstoffe), 8=Fkal (holiday shifts)
        streets = parts[0]
        strgr = parts[1]  # street sections
        strdat = parts[3]  # yearly schedule per street/section
        astdat = parts[4]  # street → ast mapping
        kal1 = parts[5]  # daily reference table (gu, vier, papier per date)
        kal2 = parts[6]  # Sperrmüll/Ast dates per (ortid, datum, ast)
        kal3 = parts[7]  # Problemstoffe dates per (ortid, datum)
        fkal = parts[8]  # holiday shifts: datum → fdatum

        # --- Resolve city ---
        ortid = _CITY_MAP.get(self._city)
        if ortid is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, list(_CITY_MAP.keys())
            )

        # --- Resolve street ---
        city_streets = [s for s in streets if s["ortid"] == ortid]
        street_map = {s["bez"]: s["id"] for s in city_streets}
        if self._street not in street_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, sorted(street_map.keys())
            )
        street_id = street_map[self._street]

        # --- Resolve street section (Strgr) ---
        sections = [s for s in strgr if s["strid"] == street_id]
        strgrid = 0
        if sections:
            if self._street_section is None:
                section_names = [s["grenze"] for s in sections]
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_section",
                    "",
                    section_names,
                )
            section_map = {s["grenze"]: s["id"] for s in sections}
            if self._street_section not in section_map:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_section",
                    self._street_section,
                    sorted(section_map.keys()),
                )
            strgrid = section_map[self._street_section]

        # --- Find schedule entry (Strdat) ---
        # Fall back to older years if no entry for current year
        current_year = datetime.date.today().year
        sd = None
        for year_offset in range(0, current_year - 2017):
            year = current_year - year_offset
            jahr = year - 2000
            candidates = [
                e
                for e in strdat
                if e["strid"] == street_id
                and e["strgrid"] == strgrid
                and e["jahr"] == jahr
            ]
            if candidates:
                sd = candidates[0]
                break
        if sd is None:
            # Fallback: any entry for this street/section
            candidates = [
                e for e in strdat if e["strid"] == street_id and e["strgrid"] == strgrid
            ]
            if not candidates:
                raise ValueError(
                    f"No schedule found for street '{self._street}'"
                    + (
                        f" section '{self._street_section}'"
                        if self._street_section
                        else ""
                    )
                )
            # Use the most recent year available
            sd = max(candidates, key=lambda e: e["jahr"])

        # --- Resolve AST number for Kal2 lookup ---
        # Kal2 uses an "ast" area code. Look it up from Astdat (part 5, i.e. parts[4]).
        # First try the exact section (strgrid), then fall back to astgrid=0
        # (street-level entry used when no section-specific ast exists).
        ast_entry = next(
            (e for e in astdat if e["strid"] == street_id and e["astgrid"] == strgrid),
            None,
        )
        if ast_entry is None and strgrid != 0:
            ast_entry = next(
                (e for e in astdat if e["strid"] == street_id and e["astgrid"] == 0),
                None,
            )
        ast = ast_entry["ast"] if ast_entry else None

        # --- Build lookup structures ---
        # Holiday shift map: original date → replacement date
        holiday_shift: dict[str, str] = {e["datum"]: e["fdatum"] for e in fkal}

        # --- Match collection dates from Kal1 ---
        # Java Calendar.DAY_OF_WEEK - 1: Sun=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
        # Python isoweekday(): Mon=1 … Sun=7  →  isoweekday() % 7 gives the same encoding
        entries: list[Collection] = []

        for entry in kal1:
            date_str: str = entry["datum"]
            gu: bool = entry["gu"]
            vier: bool = entry["vier"]
            papier: int = entry["papier"]

            d = datetime.date.fromisoformat(date_str)
            dow = d.isoweekday() % 7  # Java-compatible day-of-week

            mart = 0  # bitmask of waste types collected on this day

            # Restabfall
            if dow == sd["resttag"] and gu == sd["restgu"]:
                if not self._four_weekly_rest or vier == sd["vier"]:
                    mart |= _MART_RES

            # Bioabfall
            if dow == sd["biotag"] and gu == sd["biogu"]:
                mart |= _MART_BIO

            # Gelber Sack
            if dow == sd["werttag"] and gu == sd["wertgu"]:
                mart |= _MART_WER

            # Papier
            if papier != 0 and papier == sd["papier"]:
                mart |= _MART_PAP

            if mart == 0:
                continue

            # Apply holiday shift if applicable
            actual_date_str = holiday_shift.get(date_str, date_str)
            actual_date = datetime.date.fromisoformat(actual_date_str)

            _emit_collections(entries, actual_date, mart)

        # --- Kal2: Ast- und Strauchwerk ---
        # All Kal2 entries correspond to bitmask bit 16 (gmart_ast),
        # which the app always displays as "Ast- und Strauchwerk".
        if ast is not None:
            for entry in kal2:
                if entry["ortid"] == ortid and entry["ast"] == ast:
                    date_str = entry["datum"]
                    actual_date_str = holiday_shift.get(date_str, date_str)
                    actual_date = datetime.date.fromisoformat(actual_date_str)
                    entries.append(
                        Collection(
                            date=actual_date,
                            t="Ast- und Strauchwerk",
                            icon=ICON_MAP["Ast- und Strauchwerk"],
                        )
                    )

        # --- Kal3: Problemstoffe ---
        for entry in kal3:
            if entry["ortid"] == ortid:
                date_str = entry["datum"]
                actual_date_str = holiday_shift.get(date_str, date_str)
                actual_date = datetime.date.fromisoformat(actual_date_str)
                entries.append(
                    Collection(
                        date=actual_date,
                        t="Problemstoffe",
                        icon=ICON_MAP.get("Problemstoffe"),
                    )
                )

        return entries


def _emit_collections(
    entries: list[Collection], date: datetime.date, mart: int
) -> None:
    """Append one Collection entry per waste type in the bitmask."""
    if mart & _MART_RES:
        entries.append(
            Collection(date=date, t="Restabfall", icon=ICON_MAP["Restabfall"])
        )
    if mart & _MART_BIO:
        entries.append(Collection(date=date, t="Bioabfall", icon=ICON_MAP["Bioabfall"]))
    if mart & _MART_WER:
        entries.append(
            Collection(date=date, t="Gelber Sack", icon=ICON_MAP["Gelber Sack"])
        )
    if mart & _MART_PAP:
        entries.append(Collection(date=date, t="Papier", icon=ICON_MAP["Papier"]))
