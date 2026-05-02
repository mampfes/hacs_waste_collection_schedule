import re
from datetime import datetime

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
    extract_panel_fields,
)

TITLE = "Waipa District Council"
DESCRIPTION = (
    "Source for Waipa District Council. Finds both general and glass recycling dates."
)
URL = "https://www.waipadc.govt.nz/"
TEST_CASES = {
    "10 Queen Street": {"address": "10 Queen Street"},  # Monday
    "1 Acacia Avenue": {"address": "1 Acacia Avenue"},  # Wednesday
}

ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://waipadc.spatial.t1cloud.com",
    instance="spatial/IntraMaps",
    config_id="6aa41407-1db8-44e1-8487-0b9a08965283",
    project="b5bc138e-edce-4b01-b159-ec44539ab455",
    module_id="5373c4e1-c975-4c8f-b51a-0ac976f5313c",
    default_selection_layer="e7163a17-2f10-42b1-8dbf-8c53adf089a8",
)

# Match field names containing "Recycling" or "Glass" (they have verbose names)
RECYCLING_PATTERN = re.compile(r"Mixed Recycling", re.IGNORECASE)
GLASS_PATTERN = re.compile(r"Glass Recycling", re.IGNORECASE)

# Extract dates in format "DD-Mon-YYYY"
DATE_PATTERN = re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b")


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        try:
            with MapsClient(INTRAMAPS_CONFIG) as client:
                result = client.select_address(self._address)
        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        fields = extract_panel_fields(result["response"])

        entries = []
        for field_name, field_value in fields.items():
            if RECYCLING_PATTERN.search(field_name):
                entries.extend(self._parse_dates(field_value, "Recycling"))
            elif GLASS_PATTERN.search(field_name):
                entries.extend(self._parse_dates(field_value, "Glass"))

        return entries

    @staticmethod
    def _parse_dates(text: str, collection_type: str) -> list[Collection]:
        icon = ICON_MAP.get(collection_type)
        dates = DATE_PATTERN.findall(text)
        entries = []
        for date_str in dates:
            try:
                d = datetime.strptime(date_str, "%d-%b-%Y").date()
                entries.append(Collection(date=d, t=collection_type, icon=icon))
            except ValueError:
                continue
        return entries
