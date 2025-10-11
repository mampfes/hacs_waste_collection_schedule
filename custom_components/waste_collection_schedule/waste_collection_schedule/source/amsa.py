import datetime
from typing import Any, Dict, List, Optional, Tuple
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentRequired, SourceArgumentExceptionMultiple, SourceArgumentException
)

TITLE = "AMSA"
DESCRIPTION = "Source for AMSA (Milan, Italy) waste collection."
URL = "https://www.amsa.it/it/milano"
COUNTRY = "it"

TEST_CASES = {
    "monte_rosa_91": {
        "address": "Via Monte Rosa",
        "house_number": "91",
        "city": "Milano",
    },
    "piazza_duomo_1": {
        "address": "Piazza del Duomo",
        "house_number": "1",
        "city": "Milano",
    },
    "viale_piave_40b": {
        "address": "Viale Piave",
        "house_number": "40B",
        "city": "Milano",
    },
}

API_URL = URL + "/servizi/raccolta-differenziata?popup=services&serviceType=sdz"
ICON_MAP = {
    "indifferenziato": "mdi:trash-can",
    "organico": "mdi:leaf",
    "carta e cartone": "mdi:package-variant",
    "plastica e metallo": "mdi:recycle",
    "vetro": "mdi:bottle-soda",
}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You need to provide the street name and house number "
    "of your address, as well as the city.",
    "it": "Devi fornire il nome della via e il numero civico "
    "del tuo indirizzo, oltre alla città.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "The street name of your address in Milan "
        "(e.g., 'Via Monte Rosa').",
        "house_number": "The house number of your address in Milan "
        "(e.g., '91').",
        "city": "The city of your address (e.g., 'Milano').",
    },
    "it": {
        "address": "Il nome della via del tuo indirizzo a Milano "
        "(ad esempio, 'Via Monte Rosa').",
        "house_number": "Il numero civico del tuo indirizzo a Milano "
        "(ad esempio, '91').",
        "city": "La città del tuo indirizzo (ad esempio, 'Milano').",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
        "house_number": "House Number",
        "city": "City",
    },
    "it": {
        "address": "Indirizzo",
        "house_number": "Numero Civico",
        "city": "Città",
    }
}


class Source:
    def __init__(
        self, address: Any, house_number: Any, city: Optional[Any] = None
    ):
        """Create a new source for AMSA and validate inputs.

        Validation rules:
        - `address` is required and must be a non-empty string.
        - `house_number` is required and must be a non-empty string or int.
        - `city` is optional. If provided it must be a non-empty string.
        """

        errors: List[Tuple[str, str]] = []

        # Validate address
        if address is None or not isinstance(address, str) or address.strip() == "":
            errors.append(("address", "address must be a non-empty string"))

        # Validate house_number
        if house_number is None or not isinstance(house_number, (str, int)) or (isinstance(house_number, str) and house_number.strip() == ""):
            errors.append((
                "house_number",
                "house_number must be provided and non-empty",
            ))

        # Validate city (optional)
        if city is not None and (not isinstance(city, str) or city.strip() == ""):
            errors.append(("city", "city must be a non-empty string when provided"))

        # Raise exceptions based on validation
        if len(errors) > 1:
            arg_names = [arg for arg, _ in errors]
            message = ", ".join([f"{a}: {m}" for a, m in errors])
            raise SourceArgumentExceptionMultiple(arg_names, message)

        if len(errors) == 1:
            arg, msg = errors[0]
            if arg in ("address", "house_number"):
                raise SourceArgumentRequired(arg, msg)
            raise SourceArgumentException(arg, msg)

        # Store sanitized values
        self._address = str(address).strip()
        self._house_number = str(house_number).strip()
        self._city = str(city).strip() if city is not None else None
        self._session: Optional[requests.Session] = None

    def _build_address_query(self) -> str:
        address_query = f"{self._address} {self._house_number}"
        if self._city:
            address_query = f"{address_query}, {self._city}"
        return address_query

    def collect_waste_collection_schedule(self) -> Dict[str, List[str]]:
        """
        Fetch calendar items by emulating the site's XHR API calls (no Selenium).

        Flow (based on captured requests):
        1) POST /api/service/area-services/address-autocomplete with address
        2) POST /api/service/area-services/address-search with the chosen id
        3) POST /api/service/area-services/calendar-items with geociv (civic id)

        Returns a dict mapping ISO date strings (YYYY-MM-DD) to list of event keys (lowercase).
        """
        session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://www.amsa.it",
            "Referer": API_URL,
            "User-Agent": "Mozilla/5.0 (compatible; waste-collection-scraper/1.0)",
        }

        address_query = self._build_address_query()

        # 1) suggestions
        try:
            resp = session.post(
                "https://www.amsa.it/api/service/area-services/address-autocomplete",
                json={"address": address_query, "city": (self._city or ""), "source": "database"},
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            j = resp.json()
        except Exception as e:
            raise Exception("Could not fetch address suggestions: " + str(e)) from e

        try:
            suggestions = j.get("data", [])
            if not suggestions:
                raise Exception("No suggestions returned for address")
            suggestion = suggestions[0]
            suggestion_id = suggestion.get("id")
        except Exception as e:
            raise Exception("Could not parse suggestion response: " + str(e)) from e

        # 2) click/select suggestion -> obtain civic id / place detail
        street = suggestion.get("value") or self._address
        try:
            civic_raw = self._house_number
            try:
                civic_val = int(civic_raw)
            except Exception: # e.g. "40B". Remove non-numeric characters
                civic_val = ''.join(filter(str.isdigit, civic_raw))

            resp2 = session.post(
                "https://www.amsa.it/api/service/area-services/address-search",
                json={"id": suggestion_id, "street": suggestion.get("details", {}).get("via", street), "city": (self._city or ""), "civic": civic_val},
                headers=headers,
                timeout=15,
            )
            resp2.raise_for_status()
            j2 = resp2.json()
        except Exception as e:
            raise Exception("Could not select address / fetch place details: " + str(e)) from e

        try:
            data: Dict[str, Any] = j2.get("data") or {}
            geociv = data.get("idCivico") or data.get("place_id") or suggestion_id
            if geociv is None:
                raise Exception("No civic/place id returned from address-search")
        except Exception as e:
            raise Exception("Could not parse address-search response: " + str(e)) from e

        # 3) fetch calendar items
        try:
            resp3 = session.post(
                "https://www.amsa.it/api/service/area-services/calendar-items",
                json={"geociv": str(geociv)},
                headers=headers,
                timeout=30,
            )
            resp3.raise_for_status()
            j3 = resp3.json()
        except Exception as e:
            raise Exception("Could not fetch calendar items: " + str(e)) from e

        collections: Dict[str, List[str]] = {}
        try:
            items = j3.get("data", [])
            for item in items:
                ms = item.get("date")
                if ms is None:
                    continue
                try:
                    dt = datetime.datetime.fromtimestamp(ms / 1000.0).date()
                except Exception:
                    continue
                date_str = dt.isoformat()

                desc = (item.get("desc") or "").lower()
                if desc.startswith("raccolta "):
                    desc = desc[len("raccolta "):]
                desc = desc.strip()

                matched: List[str] = []
                for key in ICON_MAP.keys():
                    if key in desc:
                        matched.append(key)
                if not matched:
                    matched = [desc]

                existing = set(collections.get(date_str, []))
                for m in matched:
                    if m not in existing:
                        existing.add(m)
                if existing:
                    collections[date_str] = sorted(existing)
        except Exception as e:
            raise Exception("Could not parse calendar items: " + str(e)) from e

        return collections

    def fetch(self) -> List[Collection]:
        calendar_data = self.collect_waste_collection_schedule()

        entries: List[Collection] = []
        for date_str, events in calendar_data.items():
            try:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                continue
            for event in events:
                event_lower = event.lower()
                icon = ICON_MAP.get(event_lower, "mdi:trash-can")
                entries.append(Collection(date=date, t=event, icon=icon))

        entries.sort(key=lambda x: x.date)
        return entries
