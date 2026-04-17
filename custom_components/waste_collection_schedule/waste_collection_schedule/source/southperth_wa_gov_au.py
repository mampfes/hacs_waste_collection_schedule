import logging
import re
from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
    extract_panel_fields,
)

TITLE = "City of South Perth"
DESCRIPTION = "Source for City of South Perth waste collection."
URL = "https://southperth.wa.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Lansdowne Road": {"address": "156 Lansdowne Road KENSINGTON"},
    "Roebuck Drive": {"address": "13 Roebuck Drive"},
}
ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}
PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '156 Lansdowne Road KENSINGTON')",
    },
}
PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}
INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://cosp.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="29b80b8c-2c27-4a14-8f10-678c7947f7be",
    project="cf285c38-0d67-406e-93c2-35ae3d066521",
)
# Map IntraMaps field names to waste types
FIELD_MAP = {
    "Waste Pickup Day": "General Waste",
    "Next Recycling Pickup": "Recycling",
}
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            with MapsClient(INTRAMAPS_CONFIG) as client:
                result = client.select_address(self._address)
        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        response = result.get("response")
        if not isinstance(response, dict):
            raise SourceArgumentNotFound("address", self._address)

        fields = extract_panel_fields(response)
        entries: list[Collection] = []
        for field_name, waste_type in FIELD_MAP.items():
            value = fields.get(field_name, "")
            if value:
                if waste_type == "General Waste":
                    entries.extend(self._parse_schedule(value, waste_type))
                else:
                    try:
                        recycle_date = datetime.strptime(value, "%d %B %Y").date()
                    except ValueError:
                        LOGGER.warning(
                            f"'{recycle_date}' did not match expected date format."
                        )
                    entries.append(
                        Collection(
                            date=recycle_date,
                            t="Recycling",
                            icon=ICON_MAP["Recycling"],
                        )
                    )

        return entries

    @staticmethod
    def _parse_schedule(text: str, waste_type: str) -> list[Collection]:
        """Parse schedule text like 'Every Friday'."""
        icon = ICON_MAP.get(waste_type)
        text_lower = text.strip().lower()
        # "Every [Day]" — weekly
        match = re.match(r"every\s+(\w+)", text_lower)
        if match:
            weekday = WEEKDAYS.get(match.group(1))
            if weekday is not None:
                today = datetime.now().date()
                days_ahead = (weekday - today.weekday()) % 7
                next_date = today + timedelta(days=days_ahead)
                return [
                    Collection(
                        date=next_date + timedelta(weeks=i),
                        t=waste_type,
                        icon=icon,
                    )
                    for i in range(26)
                ]

        return []
