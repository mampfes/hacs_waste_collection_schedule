import difflib
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Gargždų švara"
DESCRIPTION = (
    "Source for VšĮ 'Gargždų švara' waste collection schedules "
    "(Klaipėda district municipality, Lithuania)."
)
URL = "https://www.gargzdusvara.eu"
COUNTRY = "lt"
TEST_CASES = {
    "Klemiškės I k.": {"location": "Klemiškės I k."},
    "Gargždų miesto šiaurinė dalis": {
        "location": "Gargždų m. - Aušrupio g., Gargždupio g., Lenktoji g., Lyros g., "
        "Palangos g., Rasos g., Saulažolių g., Vytenio g., Volungės g., Žibučių g."
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "location": (
            "The exact location/street-group name as shown in the 'Pasirinkite "
            "vietovę' (select location) dropdown on "
            "https://www.gargzdusvara.eu/atlieku-isvezimo-grafikai/ after picking "
            "any waste type first (e.g. 'Klemiškės I k.'). Must match exactly, "
            "including Lithuanian diacritics."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "location": "Location",
    },
}

_API_URL = "https://www.gargzdusvara.eu/ajax.php"

# API type code -> (Lithuanian display label, icon)
_WASTE_TYPES = {
    "komunalines": ("Komunalinės", Icons.GENERAL_WASTE),
    "plastikas_popietius": ("Plastikas-popierius", Icons.RECYCLING),
    "stiklas": ("Stiklas", Icons.GLASS),
    "zaliosios": ("Žaliosios", Icons.ORGANIC),
}

ICON_MAP = dict(_WASTE_TYPES.values())


class Source:
    def __init__(self, location: str):
        self._location = location

    def _fetch_locations(self, session: requests.Session, type_code: str) -> set:
        r = session.post(
            _API_URL,
            data={"action": "getLocations", "module": "Atliekos", "value": type_code},
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("status"):
            return set()
        return set(data.get("return", {}).keys())

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        entries: list[Collection] = []
        matched_any_type = False

        for type_code, (label, icon) in _WASTE_TYPES.items():
            r = session.post(
                _API_URL,
                data={
                    "action": "getDataAll",
                    "module": "Atliekos",
                    "lang": "lt",
                    "location": self._location,
                    "type": type_code,
                },
            )
            r.raise_for_status()
            data = r.json()

            if not data.get("status"):
                # This waste type has no schedule for the given location.
                continue

            matched_any_type = True
            dates = (data.get("return") or {}).get("dates") or {}
            for date_str in dates:
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
                entries.append(Collection(date=date, t=label, icon=icon))

        if not matched_any_type:
            all_locations: set = set()
            for type_code in _WASTE_TYPES:
                all_locations |= self._fetch_locations(session, type_code)
            suggestions = difflib.get_close_matches(
                self._location, sorted(all_locations), n=5, cutoff=0.5
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "location", self._location, suggestions
            )

        return entries
