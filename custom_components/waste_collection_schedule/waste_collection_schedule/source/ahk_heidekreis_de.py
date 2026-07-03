import requests
from datetime import date, timedelta

from waste_collection_schedule import Collection

TITLE = "AHK Heidekreis"
DESCRIPTION = "Source for AHK Heidekreis, Germany (ahk-heidekreis.de)"
URL = "https://www.ahk-heidekreis.de"
TEST_CASES = {
    "Munster, Wagnerstr. 10-18": {
        "city": "Munster",
        "postcode": "29633",
        "street": "Wagnerstr.",
        "house_number": "10-18",
    },
    "Walsrode, Wagnerstr.": {
        "city": "Walsrode",
        "postcode": "29664",
        "street": "Wagnerstr.",
        "house_number": "1",
    },
}

API_BASE = "https://ahkwebapi.heidekreis.de/api"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "referer": "https://ahkweb.heidekreis.de/",
    "origin": "https://ahkweb.heidekreis.de",
}

# Maps the disposal type names returned by the API to icons.
# Names have occasionally changed slightly on the API side, so matching
# is done case-insensitively and falls back to a generic bin icon.
ICON_MAP = {
    "restabfall": "mdi:trash-can",
    "gelbe tonne": "mdi:recycle",
    "bio- und gartenabfall": "mdi:leaf",
    "altpapier": "mdi:package-variant",
}

DEFAULT_ICON = "mdi:trash-can"


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


class Source:
    def __init__(self, city: str, postcode: str, street: str, house_number: str):
        self._city = str(city)
        self._postcode = str(postcode)
        self._street = str(street)
        self._house_number = str(house_number)

    def fetch(self):
        session = requests.Session()
        session.headers.update(HEADERS)

        ar_strasse = self._resolve_street_id(session)
        id_objekt = self._resolve_object_id(session, ar_strasse)
        type_names = self._get_disposal_type_names(session)
        return self._get_entries(session, id_objekt, type_names)

    def _resolve_street_id(self, session: requests.Session) -> int:
        r = session.get(
            f"{API_BASE}/QMasterData/QStreetByPartialName",
            params={"PartialName": self._street},
        )
        r.raise_for_status()
        streets = r.json()

        target_street = _normalize(self._street)
        target_postcode = self._postcode.strip()
        # City may be given as "Fallingbostel/Bad Fallingbostel" style combos
        target_city_parts = [
            _normalize(part) for part in self._city.replace(",", "/").split("/")
        ]

        matches = [
            s
            for s in streets
            if _normalize(s.get("strassenname")) == target_street
            and str(s.get("plz", "")).strip() == target_postcode
            and (
                _normalize(s.get("ort")) in target_city_parts
                or _normalize(s.get("ortOrtsteil")) in target_city_parts
                or any(
                    part in _normalize(s.get("ortOrtsteil", "")) for part in target_city_parts
                )
            )
        ]

        if not matches:
            # relax: ignore city, just match street name + postcode
            matches = [
                s
                for s in streets
                if _normalize(s.get("strassenname")) == target_street
                and str(s.get("plz", "")).strip() == target_postcode
            ]

        if not matches:
            raise Exception(
                f"No street found for street='{self._street}', "
                f"postcode='{self._postcode}', city='{self._city}'. "
                f"Check spelling against the address lookup on "
                f"https://www.ahk-heidekreis.de/fuer-privatkunden/abfuhrzeiten.html"
            )

        return matches[0]["arStrasse"]

    def _resolve_object_id(self, session: requests.Session, ar_strasse: int) -> int:
        r = session.post(
            f"{API_BASE}/QMasterData/QHouseNrEkal",
            json=[ar_strasse],
        )
        r.raise_for_status()
        house_numbers = r.json()

        target_house_number = _normalize(self._house_number)

        matches = [
            h
            for h in house_numbers
            if _normalize(h.get("hausNrHausNrZ")) == target_house_number
        ]

        if not matches:
            available = ", ".join(
                sorted({h.get("hausNrHausNrZ", "") for h in house_numbers})
            )
            raise Exception(
                f"House number '{self._house_number}' not found for this street. "
                f"Available house numbers: {available}"
            )

        return matches[0]["arObjekt"]

    def _get_disposal_type_names(self, session: requests.Session) -> dict:
        r = session.get(f"{API_BASE}/QDisposalCalendar/QDisposalTypes")
        r.raise_for_status()
        return {t["id"]: t["name"] for t in r.json()}

    def _get_entries(self, session: requests.Session, id_objekt: int, type_names: dict):
        today = date.today()
        date_from = today.strftime("%m/%d/%Y")
        date_to = (today + timedelta(days=365)).strftime("%m/%d/%Y")

        r = session.get(
            f"{API_BASE}/QDisposalCalendar/QDisposaldays",
            params={"idObject": id_objekt, "from": date_from, "to": date_to},
        )
        r.raise_for_status()
        days = r.json()

        entries = []
        for d in days:
            entry_date = date.fromisoformat(d["date"][:10])
            waste_type = type_names.get(
                d.get("idDisposalType"), f"Typ {d.get('idDisposalType')}"
            )
            icon = ICON_MAP.get(_normalize(waste_type), DEFAULT_ICON)
            entries.append(Collection(date=entry_date, t=waste_type, icon=icon))

        return entries
