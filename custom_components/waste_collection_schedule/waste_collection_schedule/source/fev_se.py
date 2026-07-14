import json
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Falu Energi & Vatten (FEV)"
DESCRIPTION = (
    "Source for Falu Energi & Vatten waste collection schedule, Falun, Sweden."
)
URL = "https://fev.se"
COUNTRY = "se"
TEST_CASES = {
    "Rådmansvägen 3": {"address": "Rådmansvägen 3"},
    "Rådmansvägen 5": {"address": "Rådmansvägen 5"},
}

ICON_MAP = {
    "Restavfall": Icons.GENERAL_WASTE,
    "Matavfall": Icons.BIO_KITCHEN,
    "Trädgårdsavfall": Icons.GARDEN,
}

PAGE_URL = "https://fev.se/atervinning/sophamtning.html"

TIMEZONE = ZoneInfo("Europe/Stockholm")

# Matches every `AppRegistry.registerInitialState('<portletId>', {...});`
# call embedded in the server-rendered page. The waste search widget's
# portlet id is treated as an implementation detail and not hardcoded here;
# instead the correct payload is identified by the presence of the
# "formAddressText" key, which is unique to the fetch-planner widget and is
# more resilient to a future re-deploy of the widget under a different
# portlet id.
STATE_RE = re.compile(
    r"registerInitialState\('[^']+',(\{.*?\})\);",
    re.DOTALL,
)

# FEV's public fetch planner only publishes the next two occurrences per
# container ("pickupDate" and "nextPickupDate"). Rather than hardcode a fixed
# cadence, the interval between those two dates is measured per container
# and used to extrapolate further future collections.
NUMBER_OF_COLLECTIONS_TO_GENERATE = 12

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to https://fev.se/atervinning/sophamtning.html, search for your "
    "address and copy the street name and house number exactly as shown in "
    "the results, e.g. 'Rådmansvägen 3'.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address including house number, exactly as it "
        "appears on fev.se, e.g. 'Rådmansvägen 3'.",
    },
}


def _to_local_date(iso_timestamp: str) -> date:
    dt_utc = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return dt_utc.astimezone(TIMEZONE).date()


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(
            PAGE_URL,
            params={"q": self._address},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        r.raise_for_status()

        state = None
        for match in STATE_RE.finditer(r.text):
            try:
                payload = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if "formAddressText" in payload:
                state = payload
                break

        if state is None:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition="the schedule page could not be parsed, it may have changed format.",
            )

        containers = state.get("containers") or []

        if not containers:
            hits = state.get("hits") or []
            if hits:
                suggestions = sorted(
                    {
                        f"{hit['PickupAddress']}, {hit.get('PickupCity', '').title()}"
                        for hit in hits
                        if hit.get("PickupAddress")
                    }
                )
                raise SourceArgumentNotFoundWithSuggestions(
                    "address", self._address, suggestions
                )
            raise SourceArgumentNotFound(
                "address",
                self._address,
            )

        entries: list[Collection] = []
        for container in containers:
            waste_type = container.get("typeText", "Unknown")
            icon = ICON_MAP.get(waste_type)

            pickup_iso = container.get("pickupDateIso")
            if not pickup_iso:
                continue
            pickup_date = _to_local_date(pickup_iso)

            next_pickup_iso = container.get("nextPickupDateIso")
            interval_days = None
            if container.get("hasNextPickup") and next_pickup_iso:
                next_pickup_date = _to_local_date(next_pickup_iso)
                interval_days = (next_pickup_date - pickup_date).days

            if not interval_days:
                entries.append(Collection(date=pickup_date, t=waste_type, icon=icon))
                continue

            for i in range(NUMBER_OF_COLLECTIONS_TO_GENERATE):
                entries.append(
                    Collection(
                        date=pickup_date + timedelta(days=interval_days * i),
                        t=waste_type,
                        icon=icon,
                    )
                )

        return entries
