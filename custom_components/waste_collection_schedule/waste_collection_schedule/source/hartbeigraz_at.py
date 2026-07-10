from __future__ import annotations

from typing import ClassVar

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Hart bei Graz"
DESCRIPTION = "Source for Hart bei Graz, Austria."
URL = "https://www.hartbeigraz.at"
COUNTRY = "at"

TEST_CASES = {
    "Am Brühlwald 15": {
        "strasse": "Am Brühlwald",
        "hausnummer": "15",
    },
    "Alois Fleck-Gasse 1": {
        "strasse": "Alois Fleck-Gasse",
        "hausnummer": "1",
    },
}

SOURCE_CODEOWNERS = ["@bbr111"]

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
    "Grün- und Strauchschnittsammlung": Icons.GARDEN,
    "Problemstoff": Icons.HAZARDOUS,
}

PARAM_TRANSLATIONS = {
    "en": {
        "strasse": "Street",
        "hausnummer": "House number",
    },
    "de": {
        "strasse": "Straße",
        "hausnummer": "Hausnummer",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Street name as listed in the Hart bei Graz waste calendar dropdown.",
        "hausnummer": "House number as listed in the Hart bei Graz waste calendar dropdown.",
    },
    "de": {
        "strasse": "Straßenname wie in der Abfallkalender-Auswahl von Hart bei Graz aufgeführt.",
        "hausnummer": "Hausnummer wie in der Abfallkalender-Auswahl von Hart bei Graz aufgeführt.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.hartbeigraz.at/Service/Muell, pick your street and "
        "house number from the dropdowns, and use the same values for "
        "'strasse' and 'hausnummer'."
    ),
    "de": (
        "Öffnen Sie https://www.hartbeigraz.at/Service/Muell, wählen Sie Ihre "
        "Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
        "dieselben Werte für 'strasse' und 'hausnummer'."
    ),
}

_MENUONR = "225225009"


class Source(RiSKommunalSource):
    BASE_URL = "https://www.hartbeigraz.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = "https://www.hartbeigraz.at/Service/Muell"
    MAX_PAGES = 25
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": _MENUONR,
        "bdatum": "31.12.9999",
    }

    def __init__(self, strasse: str, hausnummer: str | int):
        super().__init__(strasse=strasse, hausnummer=hausnummer)

    def fetch(self) -> list[Collection]:
        # The base class stops after page 1 in list mode; Hart bei Graz
        # paginates when bdatum is provided, so we handle pages manually.
        session = requests.Session()
        typids = self._resolve_typids(session)

        entries: list[Collection] = []
        seen: set[tuple[str, str]] = set()
        seen_first: set[tuple[str, str]] = set()

        for page in range(self.MAX_PAGES):
            soup = self._get_page(session, page, typids)
            rows = self._parse_list(soup)
            if not rows:
                break

            first_key = (rows[0][0].isoformat(), rows[0][1])
            if first_key in seen_first:
                break
            seen_first.add(first_key)

            for collection_date, waste_type in rows:
                key = (collection_date.isoformat(), waste_type)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=self._icon(waste_type),
                    )
                )

        return sorted(entries, key=lambda c: c.date)
