import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Cyclad"
DESCRIPTION = "Source for Cyclad waste collection, France"
URL = "https://cyclad.org"
COUNTRY = "fr"

API_COMMUNES = "https://cyclad.org/wp-json/vernalis/v1/communes"
API_CALENDAR = "https://cyclad.org/wp/wp-admin/admin-ajax.php"

TEST_CASES = {
    "Nancras by name": {"commune": "Nancras"},
    "Nancras by id": {"commune_id": 254},
}


class Source:
    def __init__(self, commune: str | None = None, commune_id: int | None = None):
        if commune is None and commune_id is None:
            raise ValueError("commune or commune_id required")
        self._commune = commune
        self._commune_id = commune_id

    def _lookup_commune_id(self) -> int:
        r = requests.get(API_COMMUNES)
        r.raise_for_status()
        communes = {c["post_title"].lower(): c["ID"] for c in r.json()}
        if self._commune is None:
            raise ValueError("commune must be provided")
        name = self._commune.lower()
        if name not in communes:
            raise SourceArgumentNotFoundWithSuggestions("commune", self._commune, communes.keys())
        return communes[name]

    def fetch(self):
        commune_id = self._commune_id or self._lookup_commune_id()
        r = requests.post(API_CALENDAR, data={"action": "ajax_calendar_autocomplete", "post_id": commune_id})
        r.raise_for_status()
        data = r.json()[0]["dates"]
        entries = []
        for waste_type, days in data.items():
            if waste_type == "intersect" or not isinstance(days, dict):
                continue
            for d in days.values():
                date = datetime.datetime.strptime(d, "%d/%m/%Y").date()
                entries.append(Collection(date=date, t=waste_type.title()))
        return entries
