import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Byron Shire Council"
DESCRIPTION = "Source for Byron Shire Council, NSW, Australia."
URL = "https://www.byron.nsw.gov.au/Residential-Services/Waste-Recycling/Bin-Collection-Services/Bin-Collection-Schedules"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Byron Shire Council, for example "
        "'120 Jonson St, Byron Bay'."
    )
}
TEST_CASES = {"120 Jonson St, Byron Bay": {"address": "120 Jonson St, Byron Bay"}}

PROJECT_ID = "592"
DISTRICT_ID = "BYSC"
ADDRESS_URL = "https://ca-web.apigw.recyclecoach.com/zone-setup/address/single"
SCHEDULE_URL = "https://ca-web.apigw.recyclecoach.com/zone-setup/zone/schedules"
COLLECTION_URL = "https://ca-web.apigw.recyclecoach.com/zone-setup/zone/collections"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://app.my-waste.mobi",
    "referer": "https://app.my-waste.mobi/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
}

ICON_MAP = {
    "garbage": "mdi:trash-can",
    "landfill": "mdi:trash-can",
    "trash": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "recycle": "mdi:recycle",
    "food": "mdi:food",
    "organics": "mdi:leaf",
    "garden": "mdi:leaf",
    "green": "mdi:leaf",
}

ZONE_ID_PATTERN = re.compile(r"(?:zone-)?z[\w-]+", re.IGNORECASE)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def fetch(self) -> list[Collection]:
        zone_id = self._get_zone_id()
        collection_types = self._get_collection_types(zone_id)
        schedule_data = self._get_schedule_data(zone_id)
        entries = self._parse_entries(schedule_data, collection_types)

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries

    def _get_zone_id(self) -> str:
        response = self._session.get(
            ADDRESS_URL,
            params={
                "sku": PROJECT_ID,
                "district": DISTRICT_ID,
                "prompt": "undefined",
                "term": self._address,
            },
            timeout=30,
        )
        response.raise_for_status()

        zone_id = self._extract_zone_id(response.json())
        if zone_id is None:
            raise SourceArgumentNotFound("address", self._address)

        return zone_id

    def _get_collection_types(self, zone_id: str) -> dict[str, str]:
        response = self._session.get(
            COLLECTION_URL,
            params={
                "project_id": PROJECT_ID,
                "district_id": DISTRICT_ID,
                "zone_id": zone_id,
                "lang_cd": "en_US",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            types = data.get("collection", {}).get("types", {})
            if isinstance(types, dict):
                return {
                    str(key): value.get("title", "")
                    for key, value in types.items()
                    if isinstance(value, dict) and value.get("title")
                }

        return {}

    def _get_schedule_data(self, zone_id: str) -> dict:
        response = self._session.get(
            SCHEDULE_URL,
            params={
                "project_id": PROJECT_ID,
                "district_id": DISTRICT_ID,
                "zone_id": zone_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _parse_entries(
        self, schedule_data: dict, collection_types: dict[str, str]
    ) -> list[Collection]:
        entries: list[Collection] = []

        for year_data in schedule_data.get("DATA", []):
            for month_data in year_data.get("months", []):
                for event in month_data.get("events", []):
                    event_date = event.get("date")
                    if not event_date:
                        continue

                    for collection in event.get("collections", []):
                        if collection.get("status") == "is_none":
                            continue

                        collection_id = collection.get("id")
                        if collection_id is None:
                            continue

                        waste_type = collection_types.get(
                            f"collection-{collection_id}"
                        ) or collection_types.get(str(collection_id))
                        if not waste_type:
                            continue

                        entries.append(
                            Collection(
                                date=datetime.strptime(event_date, "%Y-%m-%d").date(),
                                t=waste_type,
                                icon=self._guess_icon(waste_type),
                            )
                        )

        return entries

    def _extract_zone_id(self, payload) -> str | None:
        if isinstance(payload, dict):
            results = payload.get("results")
            if isinstance(results, list):
                zone_id = self._extract_zone_id_from_results(results)
                if zone_id:
                    return zone_id

            for key in ("zone_id", "zoneId", "zone", "id"):
                value = payload.get(key)
                zone_id = self._extract_zone_id(value)
                if zone_id:
                    return zone_id

            for value in payload.values():
                zone_id = self._extract_zone_id(value)
                if zone_id:
                    return zone_id

            return None

        if isinstance(payload, str):
            match = ZONE_ID_PATTERN.search(payload)
            if not match:
                return None
            zone_id = match.group(0)
            return zone_id if zone_id.startswith("zone-") else f"zone-{zone_id}"

        if isinstance(payload, list):
            for item in payload:
                zone_id = self._extract_zone_id(item)
                if zone_id:
                    return zone_id
            return None

        return None

    def _extract_zone_id_from_results(self, results: list[dict]) -> str | None:
        target = self._normalize_address(self._address)
        matches: list[dict] = []

        for result in results:
            if not isinstance(result, dict):
                continue

            address = self._normalize_address(result.get("address", ""))
            full_address = self._normalize_address(result.get("full_address", ""))
            if address == target or full_address.startswith(target):
                matches.append(result)

        for result in matches or results:
            zones = result.get("zones")
            zone_id = self._extract_zone_id(zones)
            if zone_id:
                return zone_id

        return None

    def _normalize_address(self, value: str) -> str:
        return " ".join(str(value).upper().replace(",", " ").split())

    def _guess_icon(self, waste_type: str) -> str | None:
        lower = waste_type.lower()
        for key, icon in ICON_MAP.items():
            if key in lower:
                return icon
        return None
