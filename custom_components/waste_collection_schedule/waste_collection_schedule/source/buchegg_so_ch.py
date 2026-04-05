import html
import json
import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Buchegg"
DESCRIPTION = "Source for waste collection schedule of Gemeinde Buchegg (SO), Switzerland."
URL = "https://www.buchegg-so.ch"
COUNTRY = "ch"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your locality (Ortschaft) from the list.",
    "de": "Wählen Sie Ihre Ortschaft aus der Liste.",
    "fr": "Sélectionnez votre localité dans la liste.",
    "it": "Selezionate la vostra località dalla lista.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "ortschaft": "Locality",
    },
    "de": {
        "ortschaft": "Ortschaft",
    },
    "fr": {
        "ortschaft": "Localité",
    },
    "it": {
        "ortschaft": "Località",
    },
}

TEST_CASES = {
    "Aetingen": {"ortschaft": "Aetingen"},
    "Bibern": {"ortschaft": "Bibern"},
    "Aetigkofen": {"ortschaft": "Aetigkofen"},
    "Mühledorf": {"ortschaft": "Mühledorf"},
    "Kyburg-Buchegg": {"ortschaft": "Kyburg-Buchegg"},
    "Lüterswil-Gächliwil": {"ortschaft": "Lüterswil-Gächliwil"},
}

ICON_MAP = {
    "Kehrichtabfuhr": "mdi:trash-can",
    "Grüngutabfuhr": "mdi:leaf",
}

SCRAPE_URL = "https://www.buchegg-so.ch/abfalldaten"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
    ),
}

# ============================================================
# Internal zone mapping
# ============================================================

KEHRICHT_ZONE_MAP = {
    "Aetingen": ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Brittern": ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Küttigkofen": ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Lüterswil-Gächliwil": ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Bibern": ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Gossliwil": ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Hessigkofen": ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Tscheppach": ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Aetigkofen": ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
    "Brügglen": ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
    "Kyburg-Buchegg": ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
    "Mühledorf": ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
}

GRUENGUT_GROUP_MAP = {
    "Aetigkofen":          "gross",
    "Aetingen":            "gross",
    "Bibern":              "gross",
    "Brittern":            "gross",
    "Brügglen":            "gross",
    "Gossliwil":           "gross",
    "Kyburg-Buchegg":      "gross",
    "Küttigkofen":         "gross",
    "Lüterswil-Gächliwil": "gross",
    "Hessigkofen":         "hmt",
    "Mühledorf":           "hmt",
    "Tscheppach":          "hmt",
}

GRUENGUT_GROUP_KEYWORDS = {
    "gross": {
        "keywords": ["aetigkofen", "aetingen", "bibern", "brittern", "brügglen"],
        "max_commas": None,
    },
    "hmt": {
        "keywords": ["hessigkofen", "mühledorf", "tscheppach"],
        "max_commas": 3,
    },
}


class Source:
    """Waste collection schedule for Gemeinde Buchegg (SO)."""

    def __init__(self, ortschaft: str):
        ortschaft = ortschaft.strip()

        if ortschaft not in KEHRICHT_ZONE_MAP:
            raise SourceArgumentNotFoundWithSuggestions(
                "ortschaft",
                ortschaft,
                suggestions=sorted(KEHRICHT_ZONE_MAP.keys()),
            )

        self._ortschaft = ortschaft
        self._kehricht_keywords = KEHRICHT_ZONE_MAP[ortschaft]
        self._gruengut_group = GRUENGUT_GROUP_MAP[ortschaft]

    def fetch(self) -> list[Collection]:
        """Fetch waste collection dates from the Buchegg website."""

        response = requests.get(SCRAPE_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", id="icmsTable-abfallsammlung")

        
        if not table:
            raise ValueError(
                "Table 'icmsTable-abfallsammlung' not found on page. "
                "The website structure may have changed."
            )

        entities_attr = table.get("data-entities", "")
        if not entities_attr:
            raise ValueError(
                "No 'data-entities' attribute found on table. "
                "The website structure may have changed."
            )

        try:
            entities = json.loads(html.unescape(entities_attr))
            if not isinstance(entities, dict):
                raise ValueError("Parsed 'data-entities' is not a JSON object.")
            raw_data = entities.get("data", [])
        except (json.JSONDecodeError, AttributeError, TypeError, ValueError) as err:
            raise ValueError(
                "Unable to parse table 'data-entities'. "
                "The website structure may have changed."
            ) from err

        if not raw_data:
            raise ValueError("No entries found in table data.")

        collections: list[Collection] = []

        for row in raw_data:
            name_html = row.get("name", "")
            date_html = row.get("_anlassDate", "")

            name_clean = BeautifulSoup(name_html, "html.parser").get_text(strip=True)
            name_lower = name_clean.lower()

            date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", date_html)
            if not date_match:
                continue

            entry_date = date(
                int(date_match.group(3)),
                int(date_match.group(2)),
                int(date_match.group(1)),
            )

            # --- Kehricht matching ---
            if "kehricht" in name_lower:
                if all(kw in name_lower for kw in self._kehricht_keywords):
                    collections.append(
                        Collection(
                            date=entry_date,
                            t="Kehrichtabfuhr",
                            icon=ICON_MAP.get("Kehrichtabfuhr"),
                        )
                    )

            # --- Grüngut matching ---
            elif "grüngut" in name_lower or "grünabfuhr" in name_lower:
                group = GRUENGUT_GROUP_KEYWORDS[self._gruengut_group]

                if all(kw in name_lower for kw in group["keywords"]):
                    max_commas = group.get("max_commas")
                    if max_commas and name_clean.count(",") >= max_commas:
                        continue

                    collections.append(
                        Collection(
                            date=entry_date,
                            t="Grüngutabfuhr",
                            icon=ICON_MAP.get("Grüngutabfuhr"),
                        )
                    )

        return collections
