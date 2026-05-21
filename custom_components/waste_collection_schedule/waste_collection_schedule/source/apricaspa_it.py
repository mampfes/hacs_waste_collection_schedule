import datetime
from typing import Any, Dict, List, Tuple

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Aprica S.p.A."
DESCRIPTION = "Source for Aprica S.p.A. (Gruppo A2A) waste collection."
URL = "https://www.apricaspa.it"
COUNTRY = "it"

TEST_CASES = {
    "borgo_san_giacomo_via_pascoli_18": {
        "address": "Via Giovanni Pascoli",
        "house_number": "18",
        "city": "Borgo San Giacomo",
    },
    "brescia_via_triumplina_90": {
        "address": "Via Triumplina",
        "house_number": "90",
        "city": "Brescia",
    },
    "bergamo_via_moroni_337": {
        "address": "Via Giovanni Battista Moroni",
        "house_number": "337",
        "city": "Bergamo",
    },
}

BASE_URL = "https://www.apricaspa.it"
API_URL = BASE_URL + "/it?popup=services&serviceType=sdz"

ICON_MAP = {
    "indifferenziato": Icons.GENERAL_WASTE,
    "organico": Icons.BIO_KITCHEN,
    "carta e cartone": Icons.PAPER,
    "carta": Icons.PAPER,
    "plastica": Icons.RECYCLING,
    "plastica e metallo": Icons.METAL,
    "imballaggi in plastica e metallo": Icons.METAL,
    "imballaggi in plastica": Icons.RECYCLING,
    "vetro": Icons.GLASS,
    "vetro e metallo": Icons.GLASS,
    "vetro e metalli": Icons.GLASS,
    "vetro e lattine": Icons.GLASS,
    "sfalci e potature": Icons.GARDEN,
    "verde": Icons.GARDEN,
    "tessili sanitari": Icons.TEXTILE,
    "pannolini": Icons.GENERAL_WASTE,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You need to provide the street name, house number, and city "
    "of your address. Aprica serves cities like Brescia, Bergamo, Como, "
    "Cremona, Crema, Lodi and their provinces.",
    "it": "Devi fornire il nome della via, il numero civico e la città "
    "del tuo indirizzo. Aprica serve città come Brescia, Bergamo, Como, "
    "Cremona, Crema, Lodi e relative province.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "The street name of your address (e.g., 'Via Triumplina').",
        "house_number": "The house number of your address (e.g., '90').",
        "city": "The city of your address (e.g., 'Brescia').",
    },
    "it": {
        "address": "Il nome della via del tuo indirizzo "
        "(ad esempio, 'Via Triumplina').",
        "house_number": "Il numero civico del tuo indirizzo " "(ad esempio, '90').",
        "city": "La città del tuo indirizzo (ad esempio, 'Brescia').",
    },
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
    },
}


class Source:
    def __init__(self, address: Any, house_number: Any, city: Any):
        """Create a new source for Aprica S.p.A. and validate inputs.

        Validation rules:
        - `address` is required and must be a non-empty string.
        - `house_number` is required and must be a non-empty string or int.
        - `city` is required and must be a non-empty string.
        """
        errors: List[Tuple[str, str]] = []

        # Validate address
        if address is None or not isinstance(address, str) or address.strip() == "":
            errors.append(("address", "address must be a non-empty string"))

        # Validate house_number
        if (
            house_number is None
            or not isinstance(house_number, (str, int))
            or (isinstance(house_number, str) and house_number.strip() == "")
        ):
            errors.append(
                (
                    "house_number",
                    "house_number must be provided and non-empty",
                )
            )

        # Validate city (required for Aprica, which serves multiple cities)
        if city is None or not isinstance(city, str) or city.strip() == "":
            errors.append(("city", "city is required for Aprica"))

        # Raise exceptions based on validation
        if len(errors) > 1:
            arg_names = [arg for arg, _ in errors]
            message = ", ".join([f"{a}: {m}" for a, m in errors])
            raise SourceArgumentExceptionMultiple(arg_names, message)

        if len(errors) == 1:
            arg, msg = errors[0]
            if arg in ("address", "house_number", "city"):
                raise SourceArgumentRequired(arg, msg)
            raise SourceArgumentException(arg, msg)

        # Store sanitized values
        self._address = str(address).strip()
        self._house_number = str(house_number).strip()
        self._city = str(city).strip()

    def _build_address_query(self) -> str:
        return f"{self._address} {self._house_number}, {self._city}"

    def collect_waste_collection_schedule(self) -> Dict[str, List[str]]:
        """
        Fetch calendar items by emulating the site's XHR API calls.

        Flow (same as AMSA, both are A2A group companies):
        1) POST /api/service/area-services/address-autocomplete with address
        2) POST /api/service/area-services/address-search with the chosen id
        3) POST /api/service/area-services/calendar-items with geociv (civic id)

        Returns a dict mapping ISO date strings (YYYY-MM-DD) to list of event
        keys (lowercase).
        """
        session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": BASE_URL,
            "Referer": API_URL,
            "User-Agent": "Mozilla/5.0 (compatible; waste-collection-scraper/1.0)",
        }

        address_query = self._build_address_query()

        # 1) suggestions
        try:
            resp = session.post(
                f"{BASE_URL}/api/service/area-services/address-autocomplete",
                json={
                    "address": address_query,
                    "city": self._city,
                    "source": "database",
                },
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
                raise SourceArgumentNotFound("address", self._address)
            suggestion = suggestions[0]
            suggestion_id = suggestion.get("id")
        except Exception as e:
            raise Exception("Could not parse suggestion response: " + str(e)) from e

        # 2) select suggestion -> obtain civic id / place detail
        street = suggestion.get("value") or self._address
        try:
            civic_raw = self._house_number
            try:
                civic_val = int(civic_raw)
            except Exception:  # e.g. "40B" - remove non-numeric characters
                civic_val = int("".join(filter(str.isdigit, civic_raw)))

            resp2 = session.post(
                f"{BASE_URL}/api/service/area-services/address-search",
                json={
                    "id": suggestion_id,
                    "street": suggestion.get("details", {}).get("via", street),
                    "city": self._city,
                    "civic": civic_val,
                },
                headers=headers,
                timeout=15,
            )
            resp2.raise_for_status()
            j2 = resp2.json()
        except Exception as e:
            raise Exception(
                "Could not select address / fetch place details: " + str(e)
            ) from e

        try:
            data: Dict[str, Any] = j2.get("data") or {}
            geociv = data.get("idCivico") or data.get("place_id") or suggestion_id
            if geociv is None:
                raise SourceArgumentNotFound("house_number", self._house_number)
        except Exception as e:
            raise Exception("Could not parse address-search response: " + str(e)) from e

        # 3) fetch calendar items
        try:
            resp3 = session.post(
                f"{BASE_URL}/api/service/area-services/calendar-items",
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
                    desc = desc[len("raccolta ") :]
                desc = desc.strip()

                # Prefer exact match, then longest substring match
                if desc in ICON_MAP:
                    matched = [desc]
                else:
                    # Find longest matching key to avoid subset matches
                    # e.g. "vetro e metallo" should match that key, not "vetro"
                    candidates = [key for key in ICON_MAP if key in desc]
                    if candidates:
                        matched = [max(candidates, key=len)]
                    else:
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
