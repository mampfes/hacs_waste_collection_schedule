"""Source for Geovest, Italy."""

import re
import uuid
from datetime import date, datetime, timedelta
from typing import Any, List, Optional

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "Geovest"
DESCRIPTION = "Source for Geovest, Italy."
URL = "https://geovest.bluemilk.dev"
COUNTRY = "it"

EXTRA_INFO = [
    {
        "title": "Anzola dell'Emilia",
        "default_params": {"town_id": "7"},
    },
    {
        "title": "Argelato",
        "default_params": {"town_id": "12"},
    },
    {
        "title": "Calderara di Reno",
        "default_params": {"town_id": "8"},
    },
    {
        "title": "Castel Maggiore",
        "default_params": {"town_id": "10"},
    },
    {
        "title": "Crevalcore",
        "default_params": {"town_id": "2"},
    },
    {
        "title": "Finale Emilia",
        "default_params": {"town_id": "1"},
    },
    {
        "title": "Nonantola",
        "default_params": {"town_id": "6"},
    },
    {
        "title": "Ravarino",
        "default_params": {"town_id": "9"},
    },
    {
        "title": "Sala Bolognese",
        "default_params": {"town_id": "4"},
    },
    {
        "title": "San Giovanni in Persiceto",
        "default_params": {"town_id": "5"},
    },
    {
        "title": "Sant'Agata Bolognese",
        "default_params": {"town_id": "13"},
    },
]

TEST_CASES = {
    "Via Antonio Gramsci 228": {
        "town_id": "7",
        "numbers": "228",
        "address_name": "via antonio gramsci",
    },
    "Via Oreste Vancini 3": {
        "town_id": "7",
        "numbers": "3",
        "address_name": "via oreste vancini",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "numbers": "Street Number",
        "address_name": "Street Name",
        "calendar_type_id": "Calendar Type",
        "days": "Days to fetch",
        "device_id": "Device ID (optional)",
        "authorization": "Authorization token (optional)",
    },
    "de": {
        "numbers": "Hausnummer",
        "address_name": "Straßenname",
        "calendar_type_id": "Kalendertyp",
        "days": "Tage zum Abrufen",
        "device_id": "Geräte-ID (optional)",
        "authorization": "Autorisierungstoken (optional)",
    },
    "it": {
        "numbers": "Numero Civico",
        "address_name": "Nome Strada",
        "calendar_type_id": "Tipo di calendario",
        "days": "Giorni da recuperare",
        "device_id": "ID dispositivo (opzionale)",
        "authorization": "Token di autorizzazione (opzionale)",
    },
    "fr": {
        "numbers": "Numéro de rue",
        "address_name": "Nom de la rue",
        "calendar_type_id": "Type de calendrier",
        "days": "Jours à récupérer",
        "device_id": "ID du dispositif (optionnel)",
        "authorization": "Jeton d'autorisation (optionnel)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "numbers": "Street number or house number. Defaults to 1.",
        "address_name": "Street name or address.",
        "calendar_type_id": "1 for private addresses, 2 for businesses.",
        "days": "Number of days ahead to fetch. Defaults to 30.",
        "device_id": "Optional device identifier. If omitted, a random device id is generated.",
        "authorization": "Optional Bearer token. Use this if the default token stops working.",
    },
    "de": {
        "numbers": "Hausnummer. Standardmäßig 1.",
        "address_name": "Straßenname.",
        "calendar_type_id": "1 für Privathaushalte, 2 für Unternehmen.",
        "days": "Anzahl der Tage, die abgerufen werden sollen. Standard ist 30.",
        "device_id": "Optionale Gerätekennung. Wenn sie fehlt, wird eine zufällige Geräte-ID generiert.",
        "authorization": "Optionales Bearer-Token. Verwenden Sie dies, wenn das Standard-Token nicht mehr funktioniert.",
    },
    "it": {
        "numbers": "Numero civico. Impostato su 1 per default.",
        "address_name": "Nome della strada.",
        "calendar_type_id": "1 per privati, 2 per aziende.",
        "days": "Numero di giorni da recuperare. Il valore predefinito è 30.",
        "device_id": "Identificatore dispositivo opzionale. Se omesso, viene generato un ID dispositivo casuale.",
        "authorization": "Token Bearer opzionale. Usalo se il token predefinito smette di funzionare.",
    },
    "fr": {
        "numbers": "Numéro civique. Par défaut 1.",
        "address_name": "Nom de la rue.",
        "calendar_type_id": "1 pour privé, 2 pour entreprise.",
        "days": "Nombre de jours à récupérer. La valeur par défaut est 30.",
        "device_id": "Identifiant d'appareil optionnel. Si omis, un identifiant aléatoire est généré.",
        "authorization": "Jeton Bearer optionnel. Utilisez-le si le jeton par défaut cesse de fonctionner.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Choose your town from the Geovest source menu, then search your street name. `numbers` is optional and defaults to 1 when not provided. A random `device_id` is generated automatically; enter `authorization` only if the default token stops working.",
    "it": "Scegli il tuo comune dal menu di Geovest, poi cerca il nome della strada. `numbers` è opzionale e assume il valore 1 se non fornito. Un `device_id` casuale viene generato automaticamente; inserisci `authorization` solo se il token predefinito smette di funzionare.",
}

CONFIG_FLOW_TYPES = {
    "calendar_type_id": {
        "type": "SELECT",
        "values": ["1", "2"],
        "multiple": False,
    },
}

ICON_MAP = {
    "Verde leggero": Icons.GARDEN,
    "Verde": Icons.GARDEN,
    "Organico": Icons.BIO_KITCHEN,
    "Umido": Icons.BIO_KITCHEN,
    "Indifferenziato": Icons.GENERAL_WASTE,
    "Rifiuti indifferenziati": Icons.GENERAL_WASTE,
    "Carta": Icons.PAPER,
    "Cartone": Icons.PAPER,
    "Imballaggi in plastica": Icons.PLASTIC_PACKAGING,
    "Plastica": Icons.PLASTIC_PACKAGING,
    "Metalli": Icons.METAL,
    "Vetro": Icons.GLASS,
}

AUTHORIZATION = "Bearer MTga45Xm8YAK"
USER_AGENT = "okhttp/4.9.2"
CALENDAR_TYPE_ID = "1"


class Source:
    def __init__(
        self,
        address_name: str,
        town_id: str,
        numbers: Optional[str] = None,
        calendar_type_id: str = CALENDAR_TYPE_ID,
        days: int = 30,
        device_id: Optional[str] = None,
        authorization: Optional[str] = None,
    ):
        self._address_name = address_name.strip()
        self._town_id = self._normalize_town_id(town_id)
        self._numbers = str(numbers or "1").strip()
        self._calendar_type_id = str(calendar_type_id).strip()
        self._device_id = (
            str(device_id).strip() if device_id else self._generate_device_id()
        )
        self._authorization = (
            str(authorization).strip() if authorization else AUTHORIZATION
        )
        try:
            self._days = int(days)
        except (TypeError, ValueError):
            raise SourceArgumentNotFound(
                "days",
                days,
                "Enter a positive number of days to fetch.",
            )
        self._calendar_id = None

        if self._calendar_type_id not in {"1", "2"}:
            raise SourceArgumentNotFound(
                "calendar_type_id",
                calendar_type_id,
                "Use 1 for private addresses or 2 for businesses.",
            )
        if self._days < 1:
            raise SourceArgumentNotFound(
                "days",
                days,
                "Enter a positive number of days to fetch.",
            )

    def _generate_device_id(self) -> str:
        return uuid.uuid4().hex[:16]

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "user-agent": USER_AGENT,
        }
        if self._authorization:
            headers["authorization"] = self._authorization
        return headers

    def _get_json_headers(self) -> dict[str, str]:
        headers = {
            "user-agent": USER_AGENT,
            "accept": "application/json",
            "content-type": "application/json",
        }
        if self._authorization:
            headers["authorization"] = self._authorization
        return headers

    def _search_addresses(self) -> list[dict[str, Any]]:
        url = f"{URL}/api/addresses"
        params = {
            "filter[name]": self._address_name,
            "filter[town_id]": self._town_id,
        }

        response = requests.get(
            url, params=params, headers=self._get_headers(), timeout=30
        )
        response.raise_for_status()

        data = response.json()
        addresses = data.get("addresses") or []

        if not addresses:
            raise SourceArgumentNotFound(
                "address_name",
                self._address_name,
            )

        return addresses

    def _choose_address_id(self, addresses: list[dict[str, Any]]) -> int:
        suggestions = [
            address.get("label") for address in addresses if address.get("label")
        ]
        if len(addresses) == 1:
            return int(addresses[0]["value"])

        normalized_number = self._numbers.strip()
        for address in addresses:
            label = (address.get("label") or "").lower()
            if normalized_number and re.search(
                rf"\b{re.escape(normalized_number)}\b", label
            ):
                return int(address["value"])

        raise SourceArgAmbiguousWithSuggestions(
            "address_name",
            self._address_name,
            suggestions,
        )

    def _clear_favourites(self) -> None:
        url = f"{URL}/api/favourites"
        response = requests.get(
            url,
            params={"device_id": self._device_id},
            headers=self._get_json_headers(),
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        for fav in data.get("favs", []):
            fav_id = fav.get("key")
            if fav_id is None:
                continue

            delete_url = f"{URL}/api/favourites/delete"
            delete_response = requests.post(
                delete_url,
                params={"id": fav_id, "device_id": self._device_id},
                headers=self._get_json_headers(),
                data="",
                timeout=30,
            )
            delete_response.raise_for_status()

    def _store_favourite(self, address_id: int) -> dict[str, Any]:
        url = f"{URL}/api/favourites/store"
        payload = {
            "town_id": self._town_id,
            "address_id": address_id,
            "calendar_type_id": self._calendar_type_id,
            "user_id": None,
            "device_id": self._device_id,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self._get_json_headers(),
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "ok":
            raise SourceArgumentNotFound(
                "address_name",
                self._address_name,
                "Unable to create a Geovest schedule entry for this address.",
            )

        return data

    def _get_calendar_id_from_favs(self, fav_data: dict[str, Any]) -> int | None:
        for fav in fav_data.get("favs", []):
            value = fav.get("value") or {}
            calendar_id = value.get("calendar_id")
            if calendar_id is not None:
                return int(calendar_id)
        return None

    def _fetch_favourites(self) -> dict[str, Any]:
        url = f"{URL}/api/favourites"
        response = requests.get(
            url,
            params={"device_id": self._device_id},
            headers=self._get_json_headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _normalize_town_id(self, town_id: str) -> str:
        normalized = str(town_id).strip()
        if "-" in normalized:
            normalized = normalized.split("-", 1)[0].strip()
        if not normalized.isdigit():
            raise SourceArgumentNotFound(
                "town_id",
                town_id,
                "Select the town ID from the dropdown.",
            )
        return normalized

    def _get_calendar_id(self) -> int:
        if self._calendar_id is not None:
            return self._calendar_id

        addresses = self._search_addresses()
        address_id = self._choose_address_id(addresses)

        self._clear_favourites()
        favorite_data = self._store_favourite(address_id)

        calendar_id = self._get_calendar_id_from_favs(favorite_data)
        if calendar_id is None:
            favourite_data = self._fetch_favourites()
            calendar_id = self._get_calendar_id_from_favs(favourite_data)

        if calendar_id is None:
            raise SourceArgumentNotFound(
                "address_name",
                self._address_name,
                "Could not determine a Geovest collection calendar for this address.",
            )

        self._calendar_id = calendar_id
        return calendar_id

    def _resolve_date_from_day_of_month(
        self,
        week_start: datetime,
        day_of_month: int,
        weekday_code: str,
        weekday_map: dict[str, int],
    ) -> Optional[date]:
        possible_dates = []
        for month_offset in (-1, 0, 1):
            month = week_start.month + month_offset
            year = week_start.year
            if month < 1:
                month += 12
                year -= 1
            elif month > 12:
                month -= 12
                year += 1

            try:
                candidate = datetime(year, month, day_of_month)
            except ValueError:
                continue

            if abs((candidate - week_start).days) <= 10:
                possible_dates.append(candidate.date())

        if not possible_dates:
            weekday_target = weekday_map.get(weekday_code)
            if weekday_target is None:
                return None
            delta_days = (weekday_target - week_start.weekday()) % 7
            return (week_start + timedelta(days=delta_days)).date()

        if len(possible_dates) == 1:
            return possible_dates[0]

        weekday_target = weekday_map.get(weekday_code)
        if weekday_target is not None:
            for candidate in possible_dates:
                if candidate.weekday() == weekday_target:
                    return candidate

        return possible_dates[0]

    def _fetch_week(self, calendar_id: int, date: datetime) -> list[Collection]:
        date_str = f"{date.year}-{date.month}-{date.day}"
        url = f"{URL}/api/calendar/{calendar_id}/week/{date_str}"

        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()

        data = response.json()
        wastes = data.get("wastes", {})
        week_start_raw = data.get("from")
        if not week_start_raw:
            return []

        try:
            week_start = datetime.strptime(week_start_raw.split(" ")[0], "%Y-%m-%d")
        except ValueError:
            return []

        collections: list[Collection] = []
        weekday_map = {
            "LUN": 0,
            "MAR": 1,
            "MER": 2,
            "GIO": 3,
            "VEN": 4,
            "SAB": 5,
            "DOM": 6,
        }

        for day_key, day_wastes in wastes.items():
            if not day_wastes:
                continue

            parts = day_key.split("_", 1)
            if len(parts) != 2:
                continue

            try:
                day_of_month = int(parts[0])
            except ValueError:
                continue

            weekday_code = parts[1]
            collection_date = self._resolve_date_from_day_of_month(
                week_start, day_of_month, weekday_code, weekday_map
            )
            if collection_date is None:
                continue

            for waste in day_wastes:
                waste_type = waste.get("category_name", "")
                collections.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, Icons.GENERAL_WASTE),
                    )
                )

        return collections

    def fetch(self) -> List[Collection]:
        calendar_id = self._get_calendar_id()

        today = datetime.now()
        end_date = today + timedelta(days=self._days)
        end_date_date = end_date.date()

        collections: list[Collection] = []
        current_date = today
        while current_date <= end_date:
            collections.extend(self._fetch_week(calendar_id, current_date))
            current_date += timedelta(days=7)

        return sorted(
            [
                collection
                for collection in collections
                if collection.date <= end_date_date
            ],
            key=lambda item: item.date,
        )
