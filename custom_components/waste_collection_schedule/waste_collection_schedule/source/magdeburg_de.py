import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Städtischer Abfallwirtschaftsbetrieb Magdeburg"
DESCRIPTION = "Source for SAB Magdeburg waste collection schedule."
URL = "https://www.magdeburg.de"
COUNTRY = "de"

ICS_URL = "https://st-magdeburg.server.smart-village.app/waste_calendar/export"
STREET_LIST_URL = "https://sab.ssl.metageneric.de/app/sab_i_tp/index.php"

TEST_CASES = {
    "Halberstädter Chaussee 66": {"street": "Halberstädter Chaussee 66"},
    "Agnetenstraße 10": {"street": "Agnetenstraße 10"},
}

EXTRA_INFO = [
    {
        "title": "SAB Magdeburg Abfuhrkalender",
        "url": "https://sab.ssl.metageneric.de/app/sab_i_tp/index.php",
        "country": "de",
    },
]

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Altpapier": "mdi:package-variant",
    "Gelbe Tonne": "mdi:recycle",
    "Bioabfall": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street name and house number as shown on the "
    "SAB Magdeburg website (e.g. 'Halberstädter Chaussee 66'). "
    "Search at https://sab.ssl.metageneric.de/app/sab_i_tp/index.php",
    "de": "Geben Sie Ihren Straßennamen und die Hausnummer ein, wie auf der "
    "SAB Magdeburg Webseite angezeigt (z.B. 'Halberstädter Chaussee 66'). "
    "Suchen Sie unter https://sab.ssl.metageneric.de/app/sab_i_tp/index.php",
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street and house number",
    },
    "de": {
        "street": "Straße und Hausnummer",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name and house number (e.g. 'Halberstädter Chaussee 66')",
    },
    "de": {
        "street": "Straßenname und Hausnummer (z.B. 'Halberstädter Chaussee 66')",
    },
}

PREFIX = "Abfallkalender: "


class Source:
    def __init__(self, street: str):
        if not street:
            raise SourceArgumentRequired(
                "street", "A street name and house number is required"
            )
        self._street = street.strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(
            ICS_URL,
            params={"street": self._street, "city": "Magdeburg"},
            timeout=30,
        )
        r.raise_for_status()

        # Remove DTEND lines — they use datetime format while DTSTART uses date-only,
        # which causes icalevents comparison errors. DTEND is not needed for parsing.
        ics_data = re.sub(r"DTEND:[^\r\n]+\r?\n", "", r.text)

        ics = ICS()
        dates = ics.convert(ics_data)

        if not dates:
            suggestions = self._get_street_suggestions()
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street", self._street, suggestions
                )
            raise SourceArgumentNotFound("street", self._street)

        entries = []
        for dt, waste_type in dates:
            if waste_type.startswith(PREFIX):
                waste_type = waste_type[len(PREFIX) :]

            icon = None
            for key, value in ICON_MAP.items():
                if key in waste_type:
                    icon = value
                    break

            entries.append(Collection(date=dt, t=waste_type, icon=icon))

        return entries

    def _get_street_suggestions(self) -> list[str]:
        try:
            r = requests.get(STREET_LIST_URL, timeout=15)
            r.raise_for_status()
        except Exception:
            return []

        import re

        streets = re.findall(r'option value="([^"]+)"', r.text)
        query = self._street.split()[0].lower() if self._street else ""
        return [s for s in streets if query in s.lower()][:20]
