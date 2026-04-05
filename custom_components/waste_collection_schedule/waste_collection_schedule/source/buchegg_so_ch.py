import html
import json
import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Gemeinde Buchegg"
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
        "ortschaft": "Locality (Ortschaft)",
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

PARAM_TRANSLATIONS = {
    "en": {
        "ortschaft": {
            "Aetigkofen": "Aetigkofen",
            "Aetingen": "Aetingen",
            "Bibern": "Bibern",
            "Brittern": "Brittern",
            "Brügglen": "Brügglen",
            "Gossliwil": "Gossliwil",
            "Hessigkofen": "Hessigkofen",
            "Küttigkofen": "Küttigkofen",
            "Kyburg-Buchegg": "Kyburg-Buchegg",
            "Lüterswil-Gächliwil": "Lüterswil-Gächliwil",
            "Mühledorf": "Mühledorf",
            "Tscheppach": "Tscheppach",
        },
    },
    "de": {
        "ortschaft": {
            "Aetigkofen": "Aetigkofen",
            "Aetingen": "Aetingen",
            "Bibern": "Bibern",
            "Brittern": "Brittern",
            "Brügglen": "Brügglen",
            "Gossliwil": "Gossliwil",
            "Hessigkofen": "Hessigkofen",
            "Küttigkofen": "Küttigkofen",
            "Kyburg-Buchegg": "Kyburg-Buchegg",
            "Lüterswil-Gächliwil": "Lüterswil-Gächliwil",
            "Mühledorf": "Mühledorf",
            "Tscheppach": "Tscheppach",
        },
    },
    "fr": {
        "ortschaft": {
            "Aetigkofen": "Aetigkofen",
            "Aetingen": "Aetingen",
            "Bibern": "Bibern",
            "Brittern": "Brittern",
            "Brügglen": "Brügglen",
            "Gossliwil": "Gossliwil",
            "Hessigkofen": "Hessigkofen",
            "Küttigkofen": "Küttigkofen",
            "Kyburg-Buchegg": "Kyburg-Buchegg",
            "Lüterswil-Gächliwil": "Lüterswil-Gächliwil",
            "Mühledorf": "Mühledorf",
            "Tscheppach": "Tscheppach",
        },
    },
    "it": {
        "ortschaft": {
            "Aetigkofen": "Aetigkofen",
            "Aetingen": "Aetingen",
            "Bibern": "Bibern",
            "Brittern": "Brittern",
            "Brügglen": "Brügglen",
            "Gossliwil": "Gossliwil",
            "Hessigkofen": "Hessigkofen",
            "Küttigkofen": "Küttigkofen",
            "Kyburg-Buchegg": "Kyburg-Buchegg",
            "Lüterswil-Gächliwil": "Lüterswil-Gächliwil",
            "Mühledorf": "Mühledorf",
            "Tscheppach": "Tscheppach",
        },
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
    "Aetingen":            ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Brittern":            ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Küttigkofen":         ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Lüterswil-Gächliwil": ["aetingen", "brittern", "küttigkofen", "lüterswil"],
    "Bibern":              ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Gossliwil":           ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Hessigkofen":         ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Tscheppach":          ["bibern", "gossliwil", "hessigkofen", "tscheppach"],
    "Aetigkofen":          ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
    "Brügglen":            ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
    "Kyburg-Buchegg":      ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
    "Mühledorf":           ["aetigkofen", "brügglen", "kyburg", "mühledorf"],
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
            raise Exception(
                "Table 'icmsTable-abfallsammlung' not found on page. "
                "The website structure may have changed."
            )

        entities_attr = table.get("data-entities", "")
        if not entities_attr:
            raise Exception(
                "No 'data-entities' attribute found on table. "
                "The website structure may have changed."
            )

        entities = json.loads(html.unescape(entities_attr))
        raw_data = entities.get("data", [])

        if not raw_data:
            raise Exception("No entries found in table data.")

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
