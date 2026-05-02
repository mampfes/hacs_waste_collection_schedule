from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "ASM Pavia"
DESCRIPTION = (
    "Source for ASM Pavia (porta a porta) waste collection in Pavia and "
    "surrounding municipalities, Italy."
)
URL = "https://www.asm.pv.it"
COUNTRY = "it"

TEST_CASES = {
    "Pavia, Via Piemonte": {"municipality": "Pavia", "street": "Via Piemonte"},
    "Pavia (slug), via piemonte (lowercase)": {
        "municipality": "pavia",
        "street": "via piemonte",
    },
    "Albuzzano": {"municipality": "Albuzzano", "street": "Tutte le vie"},
}

ICON_MAP = {
    "umido": "mdi:leaf",
    "carta": "mdi:paper-roll",
    "cartone": "mdi:paper-roll",
    "secco": "mdi:trash-can",
    "indifferenziato": "mdi:trash-can",
    "vetro": "mdi:bottle-soda",
    "plastica": "mdi:recycle",
    "multimateriale": "mdi:recycle",
    "verde": "mdi:tree",
    "sfalci": "mdi:tree",
    "ingombranti": "mdi:sofa",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Municipality (comune) served by ASM Pavia, e.g. 'Pavia'.",
        "street": "Street name as listed on the ASM porta-a-porta lookup. For municipalities with a single zone, use 'Tutte le vie'.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "street": "Street",
    },
    "it": {
        "municipality": "Comune",
        "street": "Via",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.asm.pv.it/raccolta-differenziata/porta-a-porta-pavia/ "
        "and pick your municipality and street from the search. Use the same "
        "values here. For small municipalities served by a single zone, use "
        "'Tutte le vie' as the street."
    ),
}

API_BASE = "https://api.asm.easyeco.prod.emberware.it/wp-json/ee/v1"


class Source:
    def __init__(self, municipality: str, street: str):
        self._municipality = str(municipality).strip()
        self._street = str(street).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})

        municipality_id = self._resolve_municipality_id(session)
        zone_id = self._resolve_zone_id(session, municipality_id)

        r = session.get(
            f"{API_BASE}/garbage-collections",
            headers={"zone-id": str(zone_id)},
            timeout=30,
        )
        r.raise_for_status()

        entries: list[Collection] = []
        for item in r.json():
            date_str = item.get("date")
            container = item.get("container-type") or {}
            title = (container.get("title") or "").strip()
            if not date_str or not title:
                continue
            collection_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            entries.append(
                Collection(
                    date=collection_date,
                    t=title,
                    icon=self._icon_for(title),
                )
            )
        return entries

    def _resolve_municipality_id(self, session: requests.Session) -> int:
        r = session.get(f"{API_BASE}/municipalities", timeout=30)
        r.raise_for_status()
        municipalities = r.json()

        target = self._municipality.casefold()
        for m in municipalities:
            if (
                str(m.get("name", "")).casefold() == target
                or str(m.get("slug", "")).casefold() == target
            ):
                return int(m["id"])

        raise SourceArgumentNotFoundWithSuggestions(
            "municipality",
            self._municipality,
            sorted(m.get("name", "") for m in municipalities if m.get("name")),
        )

    def _resolve_zone_id(self, session: requests.Session, municipality_id: int) -> int:
        r = session.get(
            f"{API_BASE}/municipalities/{municipality_id}/streets",
            params={"search": self._street},
            timeout=30,
        )
        r.raise_for_status()
        matches = r.json()

        target = self._street.casefold()
        for s in matches:
            rendered = (s.get("title") or {}).get("rendered", "")
            if rendered.casefold() == target:
                return int(s["zone-id"])

        if len(matches) == 1:
            return int(matches[0]["zone-id"])

        if len(matches) > 1:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                [(s.get("title") or {}).get("rendered", "") for s in matches],
            )

        all_streets = session.get(
            f"{API_BASE}/municipalities/{municipality_id}/streets", timeout=30
        )
        all_streets.raise_for_status()
        raise SourceArgumentNotFoundWithSuggestions(
            "street",
            self._street,
            [(s.get("title") or {}).get("rendered", "") for s in all_streets.json()],
        )

    @staticmethod
    def _icon_for(waste_type: str) -> str | None:
        lowered = waste_type.casefold()
        for key, icon in ICON_MAP.items():
            if key in lowered:
                return icon
        return None
