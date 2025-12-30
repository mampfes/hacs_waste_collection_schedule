"""Source for Abfallwirtschaft Wiener Neustadt waste collection schedule.

This source fetches waste collection schedules from abfall.wiener-neustadt.at
for municipalities in Wiener Neustadt, Austria.
"""
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Abfallwirtschaft Wiener Neustadt"
DESCRIPTION = "Source for abfall.wiener-neustadt.at waste collection schedule for Wiener Neustadt, Austria"
URL = "https://abfall.wiener-neustadt.at/"

# TEST_CASES: Each test should return a list[Collection] with date, type, and icon
# Expected waste types: Restmüll, Biotonne, Wertstoffe, Altkleider, Christbaum
TEST_CASES = {
    "Martinsgasse Monthly": {  # Returns: Restmüll (monthly) only
        "street": "Martinsgasse",
        "rm_art": "monatlich",
        "biotonne": False,
        "wertstoffe": False,
    },
    "Hauptplatz Weekly": {  # Returns: All waste types with weekly Restmüll
        "street": "Hauptplatz",
        "rm_art": "wöchentlich",
    },
    "Leithakoloniestrasse Biotonne": {  # Returns: Biotonne only
        "street": "Leithakoloniestraße",
        "restmuell": False,
        "wertstoffe": False,
        "altkleider": False,
        "christbaum": False,
    },
    "Leithakoloniestrasse Restmüll Bi-Weekly": {  # Returns: Restmüll (bi-weekly) only
        "street": "Leithakoloniestraße",
        "rm_art": "14-tägig",
        "biotonne": False,
        "wertstoffe": False,
        "altkleider": False,
        "christbaum": False,
    },
    "Leithakoloniestrasse Full": {  # Returns: All waste types with default settings
        "street": "Leithakoloniestraße",
    },
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biotonne": "mdi:leaf",
    "Wertstoffe": "mdi:recycle",
    "Altpapier": "mdi:package-variant",
    "Altkleider": "mdi:tshirt-crew",
    "Christbaum": "mdi:pine-tree",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the website https://abfall.wiener-neustadt.at/ and select your street from the dropdown menu. Note your street name and select the waste collection frequency that applies to your address.",
    "de": "Besuchen Sie die Website https://abfall.wiener-neustadt.at/ und wählen Sie Ihre Straße aus dem Dropdown-Menü. Notieren Sie sich Ihren Straßennamen und wählen Sie die Abfuhrhäufigkeit, die für Ihre Adresse gilt.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name in Wiener Neustadt (e.g., 'Martinsgasse', 'Hauptplatz')",
        "str_id": "Optional: Street ID if known (skips street lookup)",
        "rm_art": "Collection frequency for residual waste: 'wöchentlich' (weekly), '14-tägig' (bi-weekly), or 'monatlich' (monthly)",
        "restmuell": "Include residual waste (Restmüll) collection dates",
        "biotonne": "Include organic waste (Biotonne) collection dates",
        "wertstoffe": "Include recyclables (Wertstoffe / Yellow Bag) collection dates",
        "altkleider": "Include textile (Altkleider) collection dates",
        "christbaum": "Include Christmas tree collection dates",
    },
    "de": {
        "street": "Straßenname in Wiener Neustadt (z.B. 'Martinsgasse', 'Hauptplatz'). Die Straße muss exakt so geschrieben werden, wie sie auf der Website erscheint.",
        "str_id": "Optional: Straßen-ID falls bekannt. Wenn angegeben, wird die Straßensuche übersprungen.",
        "rm_art": "Abfuhrhäufigkeit für Restmüll. Wählen Sie 'wöchentlich' für wöchentliche Abfuhr, '14-tägig' für zweiwöchentliche Abfuhr, oder 'monatlich' für monatliche Abfuhr.",
        "restmuell": "Abfuhrtermine für Restmüll anzeigen. Hinweis: Die Häufigkeit wird über 'rm_art' gesteuert.",
        "biotonne": "Abfuhrtermine für die Biotonne (Organik-Abfall) anzeigen. Diese Termine werden zusätzlich zu den Restmüllterminen abgerufen.",
        "wertstoffe": "Abfuhrtermine für Wertstoffe (Gelber Sack / Gelbe Tonne) anzeigen. Beinhaltet Verpackungen aus Kunststoff, Metall und Verbundmaterialien.",
        "altkleider": "Abfuhrtermine für Altkleider und Textilien anzeigen. Diese Sammlungen finden in der Regel seltener statt.",
        "christbaum": "Abfuhrtermine für Christbäume anzeigen. Diese Sammlung findet üblicherweise nur im Januar statt.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street Name",
        "str_id": "Street ID",
        "rm_art": "Collection Frequency",
        "restmuell": "Residual Waste",
        "biotonne": "Organic Waste (Biotonne)",
        "wertstoffe": "Recyclables (Wertstoffe)",
        "altkleider": "Textiles",
        "christbaum": "Christmas Tree",
    },
    "de": {
        "street": "Straße",
        "str_id": "Straßen-ID",
        "rm_art": "Abfuhrhäufigkeit (Restmüll)",
        "restmuell": "Restmüll",
        "biotonne": "Biotonne (Organik)",
        "wertstoffe": "Wertstoffe (Gelber Sack)",
        "altkleider": "Altkleider (Textilien)",
        "christbaum": "Christbaum",
    },
}

# Map user-friendly frequency names to internal codes
# Website codes: 31=wöchentlich, 33=14-tägig, 36=monatlich
RM_ART_MAP = {
    "wöchentlich": "31",
    "weekly": "31",
    "31": "31",
    "14-tägig": "33",
    "2weeks": "33",
    "bi-weekly": "33",
    "33": "33",
    "monatlich": "36",
    "monthly": "36",
    "36": "36",
}

CONFIG_FLOW_TYPES = {
    "rm_art": {
        "type": "SELECT",
        "values": ["wöchentlich", "14-tägig", "monatlich"],
        "multiple": False,
    },
    "restmuell": {"type": "BOOL"},
    "biotonne": {"type": "BOOL"},
    "wertstoffe": {"type": "BOOL"},
    "altkleider": {"type": "BOOL"},
    "christbaum": {"type": "BOOL"},
}


class Source:
    def __init__(
        self,
        street: str,
        str_id: str | None = None,
        rm_art: str = "monatlich",
        restmuell: bool = True,
        biotonne: bool = True,
        wertstoffe: bool = True,
        altkleider: bool = True,
        christbaum: bool = True,
    ):
        """Initialize the Wiener Neustadt waste collection source.
        
        Args:
            street: Street name in Wiener Neustadt
            str_id: Optional street ID (if known, skips street lookup)
            rm_art: Collection frequency: 'wöchentlich', '14-tägig', or 'monatlich'
            restmuell: Include residual waste collection dates (default: True)
            biotonne: Include organic waste collection dates (default: True)
            wertstoffe: Include recyclables collection dates (default: True)
            altkleider: Include textile collection dates (default: True)
            christbaum: Include Christmas tree collection dates (default: True)
            
        Note:
            rm_art controls the frequency of Restmüll collection, but Restmüll can be
            filtered out by setting restmuell=False.
        """
        self._street = street
        self._str_id = str_id
        self._rm_art = RM_ART_MAP.get(rm_art.lower(), "36")  # Default to monthly
        self._restmuell = restmuell
        self._biotonne = biotonne
        self._wertstoffe = wertstoffe
        self._altkleider = altkleider
        self._christbaum = christbaum
        self._base_url = "https://abfall.wiener-neustadt.at"

    def fetch(self) -> list[Collection]:
        """Fetch waste collection schedule for Wiener Neustadt.
        
        Returns:
            List of Collection objects
            
        Raises:
            Exception: If street not found or data cannot be retrieved
        """
        # Step 1: Get street ID if not provided
        if not self._str_id:
            self._str_id, str_name_full, tn_ez_zone = self._lookup_street()
        else:
            str_name_full = None
            tn_ez_zone = None

        # Step 2: Fetch collection schedule
        entries = self._fetch_schedule(self._str_id, str_name_full, tn_ez_zone)
        
        # Step 3: Filter out unwanted waste types
        if not self._restmuell:
            entries = [e for e in entries if e.type != "Restmüll"]
        
        return entries

    def _lookup_street(self) -> tuple[str, str | None, str | None]:
        """Look up street ID from street name using the ASP backend.
        
        Returns:
            Tuple of (street_id, full_street_name, tn_ez_zone)
            
        Raises:
            SourceArgumentNotFoundWithSuggestions: If street not found
        """
        # The website uses vb_wn_termine.asp with street selection
        # Step 1: Determine first letter for page loading
        current_year = datetime.now().year
        first_letter = self._street[0].upper() if self._street else 'A'
        
        # Step 2: Load initial page with first letter to get street dropdown
        initial_url = f"{self._base_url}/vb_wn_termine.asp?bst={first_letter}&jahr={current_year}"
        try:
            response = requests.get(initial_url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Failed to connect to {self._base_url}. "
                f"Please check your internet connection and verify the website is accessible. Error: {e}"
            )
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Step 3: Find street in select/option elements
        str_id = None
        str_name_full = None
        tn_ez_zone = None
        
        street_normalized = self._street.lower().replace("ß", "ss").replace("ä", "a").replace("ö", "o").replace("ü", "u")
        
        found_streets = []  # For suggestions if exact match fails
        
        for select in soup.find_all("select", {"name": "str_id"}):
            for option in select.find_all("option"):
                option_text = option.get_text().strip()
                option_value = option.get("value", "").strip()
                
                if not option_value or option_value == "0":
                    continue
                    
                option_normalized = option_text.lower().replace("ß", "ss").replace("ä", "a").replace("ö", "o").replace("ü", "u")
                found_streets.append((option_text, option_value))
                
                # Try exact match or starts-with match
                if street_normalized == option_normalized or option_normalized.startswith(street_normalized):
                    str_id = option_value
                    str_name_full = option_text
                    break
            if str_id:
                break
        
        if not str_id:
            # Try partial match if exact match failed
            for option_text, option_value in found_streets:
                option_normalized = option_text.lower().replace("ß", "ss").replace("ä", "a").replace("ö", "o").replace("ü", "u")
                if street_normalized in option_normalized:
                    str_id = option_value
                    str_name_full = option_text
                    break
        
        if not str_id:
            # Street not found - provide suggestions
            suggestions = [s[0] for s in found_streets[:20]]
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                suggestions,
            )
        
        # Step 4: Extract tn_ez_zone from hidden input (if present)
        tn_ez_zone_input = soup.find("input", {"name": "tn_ez_zone", "type": "hidden"})
        if tn_ez_zone_input:
            tn_ez_zone = tn_ez_zone_input.get("value")
        
        # Step 5: Reload page with selected street to get correct tn_ez_zone
        try:
            reload_response = requests.post(initial_url, data={"str_id": str_id}, timeout=30)
            reload_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Failed to retrieve zone information for street '{str_name_full}'. "
                f"The website may be temporarily unavailable. Error: {e}"
            )
        
        reload_soup = BeautifulSoup(reload_response.text, "html.parser")
        tn_ez_zone_input = reload_soup.find("input", {"name": "tn_ez_zone", "type": "hidden"})
        if tn_ez_zone_input:
            tn_ez_zone = tn_ez_zone_input.get("value")
        
        # Also get str_name from hidden input if present
        str_name_input = reload_soup.find("input", {"name": "str_name", "type": "hidden"})
        if str_name_input:
            str_name_full = str_name_input.get("value")
        
        return (str_id, str_name_full, tn_ez_zone)

    def _fetch_schedule(
        self,
        str_id: str,
        str_name_full: str | None,
        tn_ez_zone: str | None,
    ) -> list[Collection]:
        """Fetch and parse the waste collection schedule.
        
        Args:
            str_id: Street ID
            str_name_full: Full street name (optional)
            tn_ez_zone: Zone information (optional)
            
        Returns:
            List of Collection objects
        """
        # Determine year - use next year if we're in December
        current_year = datetime.now().year
        if datetime.now().month == 12:
            year = current_year + 1
        else:
            year = current_year
        
        # Determine first letter parameter for URL
        if str_name_full:
            first_letter = str_name_full[0].upper()
        else:
            first_letter = self._street[0].upper()
        
        # Map letter to numeric code if needed (usually not required, but kept for compatibility)
        # Build POST request URL
        post_url = f"{self._base_url}/vb_wn_termine.asp?bst={first_letter}&jahr={year}"
        
        # Build form data
        post_data = {
            "str_id": str_id,
            "rm_art": self._rm_art,
        }
        
        if tn_ez_zone:
            post_data["tn_ez_zone"] = tn_ez_zone
        if str_name_full:
            post_data["str_name"] = str_name_full
        
        # Add waste type checkboxes
        if self._biotonne:
            post_data["chk_biotonne"] = "ja"
        if self._wertstoffe:
            post_data["chk_wertstoffe"] = "ja"
        if self._altkleider:
            post_data["chk_altkleider"] = "ja"
        if self._christbaum:
            post_data["chk_christbaum"] = "ja"
        
        # Submit form
        try:
            response = requests.post(post_url, data=post_data, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Failed to fetch collection schedule for street ID '{str_id}'. "
                f"The website may be temporarily unavailable or the street ID is invalid. Error: {e}"
            )
        
        # Parse response
        return self._parse_schedule(response.text)

    def _parse_schedule(self, html: str) -> list[Collection]:
        """Parse collection schedule from HTML response.
        
        Args:
            html: HTML response text
            
        Returns:
            List of Collection objects
            
        Raises:
            Exception: If no collection dates found
        """
        entries = []
        
        # Try multiple regex patterns for robustness
        patterns = [
            r'<div[^>]*>\s*(\d{2})\.(\d{2})\.(\d{4})\s*&nbsp;\s*([^<]+)</div>',
            r'<div[^>]*>\s*(\d{2})\.(\d{2})\.(\d{4})\s+\xa0\s*([^<]+)</div>',
            r'<div[^>]*>\s*(\d{2})\.(\d{2})\.(\d{4})\s+([^<]+)</div>',
            r'<div[^>]*padding:3px[^>]*>\s*(\d{2})\.(\d{2})\.(\d{4})\s*[&\s\xa0]+([^<]+)</div>',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            
            for match in matches:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                waste_text = match.group(4).strip()
                
                # Map waste type text to standard names
                waste_type = self._normalize_waste_type(waste_text)
                
                if waste_type:
                    try:
                        date_obj = datetime(year, month, day).date()
                        entries.append(
                            Collection(
                                date=date_obj,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )
                    except ValueError as e:
                        # Invalid date (e.g., 31.02.2025), skip this entry
                        # This can happen with malformed HTML or parsing errors
                        continue
            
            # If we found entries with this pattern, stop trying others
            if entries:
                break
        
        if not entries:
            raise Exception(
                f"No collection dates found for street '{self._street}'. "
                "The website structure may have changed or no data is available for this address. "
                "Please verify your street name on https://abfall.wiener-neustadt.at/"
            )
        
        # Filter future dates only and sort
        today = datetime.now().date()
        filtered_entries = [entry for entry in entries if entry.date >= today]
        return sorted(filtered_entries, key=lambda x: x.date)

    @staticmethod
    def _normalize_waste_type(waste_text: str) -> str | None:
        """Normalize waste type text to standard names.
        
        Args:
            waste_text: Raw waste type text from website
            
        Returns:
            Normalized waste type name or None if not recognized
        """
        waste_lower = waste_text.lower()
        
        # Check specific types FIRST before generic patterns
        # Order matters: check "bio" before "müll" to avoid misclassifying "Biomüll"
        if "bio" in waste_lower:
            return "Biotonne"
        elif "christbaum" in waste_lower or "tannenbaum" in waste_lower:
            return "Christbaum"
        elif "wertstoff" in waste_lower or "gelb" in waste_lower:
            return "Wertstoffe"
        elif "papier" in waste_lower:
            return "Altpapier"
        elif "kleider" in waste_lower or "textil" in waste_lower:
            return "Altkleider"
        # Check "rest" and "müll" LAST as they are generic
        elif any(x in waste_lower for x in ["rest", "müll", "m�ll"]):
            return "Restmüll"
        
        return None
