import html
import json
import logging
import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Buchegg"
DESCRIPTION = (
    "Source for waste collection schedule of Gemeinde Buchegg (SO), Switzerland."
)
URL = "https://www.buchegg-so.ch"
COUNTRY = "ch"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your village from the list.",
    "de": "Wählen Sie Ihre Ortschaft aus der Liste.",
    "fr": "Sélectionnez votre localité dans la liste.",
    "it": "Selezionate la vostra località dalla lista.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "locality": "Village",
    },
    "de": {
        "locality": "Ortschaft",
    },
    "fr": {
        "locality": "Localité",
    },
    "it": {
        "locality": "Località",
    },
}

TEST_CASES = {
    "Aetingen": {"locality": "Aetingen"},
    "Bibern": {"locality": "Bibern"},
    "Aetigkofen": {"locality": "Aetigkofen"},
    "Mühledorf": {"locality": "Mühledorf"},
    "Kyburg-Buchegg": {"locality": "Kyburg-Buchegg"},
    "Lüterswil-Gächliwil": {"locality": "Lüterswil-Gächliwil"},
    "Gossliwil": {"locality": "Gossliwil"},
    "Tscheppach (deprecated ortschaft param)": {"ortschaft": "Tscheppach"},
}

ICON_MAP = {
    "Kehrichtabfuhr": "mdi:trash-can",
    "Grüngutabfuhr": "mdi:leaf",
    "Altpapier": "mdi:newspaper-variant-outline",
}

BUCHEGG_URL = "https://www.buchegg-so.ch/abfalldaten"
LOCALCITIES_URL = "https://www.localcities.ch/de/entsorgung/buchegg/3385"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
    ),
}

# ============================================================
# All villages within Gemeinde Buchegg
# ============================================================

VILLAGES = [
    "Aetigkofen",
    "Aetingen",
    "Bibern",
    "Brittern",
    "Brügglen",
    "Gossliwil",
    "Hessigkofen",
    "Küttigkofen",
    "Kyburg-Buchegg",
    "Lüterswil-Gächliwil",
    "Mühledorf",
    "Tscheppach",
]

# ============================================================
# Household waste: each village maps to a set of zone-matching
# keywords used to identify the correct schedule entry.
# ============================================================

HOUSEHOLD_WASTE_ZONE_MAP = {
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

# ============================================================
# Green waste: each village belongs to one of two collection
# groups. "default" covers 9 villages, "reduced" covers
# Hessigkofen, Mühledorf and Tscheppach which have a separate
# schedule with fewer collection dates.
# ============================================================

GREEN_WASTE_GROUP_MAP = {
    "Aetigkofen": "default",
    "Aetingen": "default",
    "Bibern": "default",
    "Brittern": "default",
    "Brügglen": "default",
    "Gossliwil": "default",
    "Kyburg-Buchegg": "default",
    "Küttigkofen": "default",
    "Lüterswil-Gächliwil": "default",
    "Hessigkofen": "reduced",
    "Mühledorf": "reduced",
    "Tscheppach": "reduced",
}

GREEN_WASTE_GROUP_KEYWORDS: dict[str, dict[str, list[str] | int | None]] = {
    "default": {
        "keywords": ["aetigkofen", "aetingen", "bibern", "brittern", "brügglen"],
        "max_commas": None,
    },
    "reduced": {
        "keywords": ["hessigkofen", "mühledorf", "tscheppach"],
        "max_commas": 3,
    },
}

# ============================================================
# Waste paper: village name to LocalCities display name mapping.
# LocalCities uses "SO" suffixes for cantonal disambiguation.
# ============================================================

VILLAGE_TO_LOCALCITIES = {
    "Aetigkofen": "Aetigkofen",
    "Aetingen": "Aetingen",
    "Bibern": "Bibern SO",
    "Brittern": "Brittern",
    "Brügglen": "Brügglen",
    "Gossliwil": "Gossliwil",
    "Hessigkofen": "Hessigkofen",
    "Küttigkofen": "Küttigkofen",
    "Kyburg-Buchegg": "Kyburg-Buchegg",
    "Lüterswil-Gächliwil": "Lüterswil",
    "Mühledorf": "Mühledorf SO",
    "Tscheppach": "Tscheppach",
}


class Source:
    """Waste collection schedule for Gemeinde Buchegg (SO)."""

    def __init__(
        self,
        locality: str | None = None,
        ortschaft: str | None = None,
    ):
        """Initialize with village name.

        Accepts 'locality' (preferred) or the deprecated 'ortschaft'
        parameter for backward compatibility.
        """
        if locality and ortschaft:
            raise ValueError(
                "Both 'locality' and 'ortschaft' are set. "
                "Please use only 'locality'."
            )

        if ortschaft:
            _LOGGER.warning(
                "Parameter 'ortschaft' is deprecated and will be removed "
                "in a future version. Please use 'locality' instead."
            )
            village = ortschaft.strip()
        elif locality:
            village = locality.strip()
        else:
            raise SourceArgumentNotFoundWithSuggestions(
                "locality",
                "",
                suggestions=VILLAGES,
            )

        if village not in VILLAGES:
            raise SourceArgumentNotFoundWithSuggestions(
                "locality",
                village,
                suggestions=VILLAGES,
            )

        self._village = village
        self._waste_zone_keywords = HOUSEHOLD_WASTE_ZONE_MAP[village]
        self._green_waste_group = GREEN_WASTE_GROUP_MAP[village]

    def fetch(self) -> list[Collection]:
        """Fetch waste collection dates from all configured providers."""
        collections: list[Collection] = []
        collections.extend(self._fetch_household_and_green_waste())
        collections.extend(self._fetch_waste_paper())
        return collections

    def _fetch_household_and_green_waste(self) -> list[Collection]:
        """Fetch household waste and green waste dates from buchegg-so.ch."""
        response = requests.get(BUCHEGG_URL, headers=HEADERS, timeout=30)
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

            if "kehricht" in name_lower:
                if all(kw in name_lower for kw in self._waste_zone_keywords):
                    collections.append(
                        Collection(
                            date=entry_date,
                            t="Kehrichtabfuhr",
                            icon=ICON_MAP.get("Kehrichtabfuhr"),
                        )
                    )

            elif "grüngut" in name_lower or "grünabfuhr" in name_lower:
                group = GREEN_WASTE_GROUP_KEYWORDS[self._green_waste_group]

                keywords = group["keywords"]
                assert isinstance(keywords, list)
                if all(kw in name_lower for kw in keywords):
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

    def _fetch_waste_paper(self) -> list[Collection]:
        """Fetch waste paper (Altpapier) dates from localcities.ch.

        Paginates through all available pages and extracts entries
        matching the configured village.

        Network errors are caught gracefully so that data from other
        providers is still returned. Entries with unexpected or invalid
        date formats may be skipped during parsing.
        """
        collections: list[Collection] = []
        localcities_name = VILLAGE_TO_LOCALCITIES.get(self._village)

        if localcities_name is None:
            return collections

        page = 1
        while True:
            url = LOCALCITIES_URL
            if page > 1:
                url = f"{LOCALCITIES_URL}?page={page}"

            try:
                response = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=30,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                _LOGGER.warning(
                    "Failed to fetch LocalCities waste paper data from %s: %s",
                    url,
                    exc,
                )
                # Network/HTTP error – return what we have so far
                break

            soup = BeautifulSoup(response.text, "html.parser")
            result_list = soup.find("div", attrs={"data-js-result-list": True})
            if result_list is None:
                break

            date_rows = result_list.find_all("div", class_="row", recursive=False)
            if not date_rows:
                break

            for row in date_rows:
                date_col = row.find("div", class_="waste-calender-list__date")
                if date_col is None:
                    continue
                date_heading = date_col.find(["h2", "h3"])
                if date_heading is None:
                    continue

                date_text = date_heading.get_text(strip=True)
                year = self._find_year_for_date(result_list, row)

                try:
                    entry_date = datetime.strptime(
                        f"{date_text}.{year}", "%d.%m.%Y"
                    ).date()
                except ValueError:
                    continue

                waste_items = row.find_all(
                    "div",
                    class_=re.compile(r"waste-calendar-list-item-small"),
                )

                for waste_item in waste_items:
                    css_classes = " ".join(waste_item.get("class", []))
                    if "waste-paper" not in css_classes:
                        continue

                    # Extract locality text (strip img alt-text prefix)
                    item_text = waste_item.get_text(strip=True)
                    for prefix in ["Altpapier", "Papier", "Paper"]:
                        if item_text.startswith(prefix):
                            item_text = item_text[len(prefix) :].strip()
                            break

                    if item_text == localcities_name:
                        collections.append(
                            Collection(
                                date=entry_date,
                                t="Altpapier",
                                icon=ICON_MAP.get("Altpapier"),
                            )
                        )

            # Check for pagination button
            load_more = soup.find(
                "input",
                attrs={"data-js-results-load-more-next-page": True},
            )
            if load_more is None:
                break

            next_page_str = load_more.get("data-js-results-load-more-next-page", "")
            try:
                next_page = int(next_page_str)
            except ValueError:
                break

            if next_page <= page:
                break

            page = next_page

        return collections

    @staticmethod
    def _find_year_for_date(result_list, current_row) -> int:
        """Extract the year from the nearest preceding month/year heading.

        LocalCities displays dates as DD.MM with separate month headings
        like 'April <span>2026</span>' above each group of date rows.
        """
        children = list(result_list.children)
        current_year = datetime.now().year
        last_year = current_year

        for child in children:
            if child == current_row:
                return last_year

            if hasattr(child, "name") and child.name == "h1":
                headline_class = child.get("class", [])
                if any("calendar-list__headline" in c for c in headline_class):
                    span = child.find("span")
                    if span:
                        try:
                            last_year = int(span.get_text(strip=True))
                        except ValueError:
                            pass

        return last_year
