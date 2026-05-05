import re
from datetime import date, datetime, timedelta
from urllib.parse import quote

import requests
from waste_collection_schedule import Collection

TITLE = "City of Oklahoma City"
DESCRIPTION = (
    "Source for data.okc.gov and okc.schizo.dev services for City of Oklahoma City"
)
URL = "https://data.okc.gov"
COUNTRY = "us"
TEST_CASES = {
    "Test_001": {"objectID": "1781151"},
    "Test_002": {"objectID": "2002902"},
    "Test_003": {"objectID": 1935340},
}
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en,en-GB;q=0.7,en-US;q=0.3",
    "Upgrade-Insecure-Requests": "1",
}
API_BASE_URL = "https://data.okc.gov/services/portal/api/data/records"
UNOFFICIAL_URL = "https://okc.schizo.dev/trash"
DATASET_BY_TYPE = {
    "TRASH": "trash zones",
    "BULKY": "bulky waste zones",
    "RECYCLE": "recycle zones",
}
WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
ICON_MAP = {
    "TRASH": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "BULKY": "mdi:sofa",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "objectID": "Object ID for unofficial source (okc.schizo.dev).",
        "try_official": "If checked, use official data.okc.gov zone datasets and the three Object IDs below.",
        "bulkyObjectID": "Object ID from 'Bulky Waste Zones'.",
        "recycleObjectID": "Object ID from 'Recycle Zones'.",
        "trashObjectID": "Object ID from 'Trash Zones'.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Using your browser, go to https://data.okc.gov/portal/page/viewer?datasetName=Bulky%20Waste%20Zones&view=map and search for your address. "
    "Go to the table tab and filter by address. Find your Object ID. "
    "Next use the dropdown in the top right hand side of the screen to change the dataset from Bulky Waste Zones to Recycle Zones. "
    "Once again Filter by Map to find your Object ID. Do this once more for your Trash Zone. "
    "Once you have these three Object IDs, enter them in bulkyObjectID, recycleObjectID, and trashObjectID and enable try_official. "
    "If try_official is disabled, provide objectID for the unofficial source."
}


class Source:
    def __init__(
        self,
        objectID: str = "",
        try_official: bool = False,
        bulkyObjectID: str = "",
        recycleObjectID: str = "",
        trashObjectID: str = "",
    ):
        if isinstance(try_official, bool):
            self._try_official = try_official
        else:
            self._try_official = str(try_official).strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        self._object_id = str(objectID).strip()
        self._record_ids = {
            "BULKY": str(bulkyObjectID).strip(),
            "RECYCLE": str(recycleObjectID).strip(),
            "TRASH": str(trashObjectID).strip(),
        }

        if self._try_official:
            missing = [
                waste_type
                for waste_type, record_id in self._record_ids.items()
                if record_id == ""
            ]
            if missing:
                raise Exception(
                    "Missing official Object IDs for: "
                    + ", ".join(missing)
                    + ". Provide bulkyObjectID, recycleObjectID, trashObjectID."
                )
        elif self._object_id == "":
            raise Exception(
                "objectID is required when try_official is disabled (unofficial source mode)."
            )

    def _fetch_rows(self, dataset_name: str, params: dict[str, str]):
        dataset_path = quote(dataset_name, safe="")
        response = requests.get(
            f"{API_BASE_URL}/{dataset_path}",
            params=params,
            headers=HEADERS,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "html" in content_type:
            raise Exception(
                f"Official source blocked or returned HTML instead of JSON for dataset '{dataset_name}'. "
                "This endpoint is protected in some environments."
            )

        try:
            json_data = response.json()
        except Exception as e:
            raise Exception(
                f"Invalid response returned from source: {API_BASE_URL}/{dataset_path}"
            ) from e

        records = json_data.get("Records")
        if records is None:
            records = json_data.get("records")

        fields = json_data.get("Fields")
        if fields is None:
            fields = json_data.get("fields", [])

        if not isinstance(records, list):
            return []

        rows = []
        for record in records:
            if len(record) != len(fields):
                continue
            rows.append(
                {
                    str(field.get("FieldName", "")): value
                    for field, value in zip(fields, record)
                }
            )

        return rows

    def _fetch_record(self, dataset_name: str, record_id: str):
        rows = self._fetch_rows(dataset_name, {"recordID": record_id})
        if not rows:
            raise Exception(
                f"No records found for Object ID {record_id} in dataset '{dataset_name}'."
            )
        return rows[0]

    def _next_weekday(self, weekday_name: str, today: date) -> date:
        target_weekday = WEEKDAY_INDEX[weekday_name.lower()]
        days_ahead = (target_weekday - today.weekday()) % 7
        return today + timedelta(days=days_ahead)

    def _nth_weekday_of_month(
        self, year: int, month: int, weekday_index: int, nth: int
    ) -> date | None:
        first_day = date(year, month, 1)
        delta_to_weekday = (weekday_index - first_day.weekday()) % 7
        candidate = first_day + timedelta(days=delta_to_weekday + (nth - 1) * 7)
        if candidate.month != month:
            return None
        return candidate

    def _next_nth_weekday(self, nth: int, weekday_name: str, today: date) -> date:
        weekday_index = WEEKDAY_INDEX[weekday_name.lower()]
        year = today.year
        month = today.month

        for _ in range(24):
            candidate = self._nth_weekday_of_month(year, month, weekday_index, nth)
            if candidate is not None and candidate >= today:
                return candidate

            month += 1
            if month > 12:
                month = 1
                year += 1

        raise Exception(
            f"Unable to calculate next '{nth}' '{weekday_name}' date from {today}."
        )

    def _resolve_pickup_date(self, pickup_rule: str, today: date) -> date:
        normalized_rule = pickup_rule.strip()
        normalized_rule_lower = normalized_rule.lower()

        if normalized_rule_lower in WEEKDAY_INDEX:
            return self._next_weekday(normalized_rule_lower, today)

        ordinal_match = re.match(
            r"^(?P<nth>[1-5])(st|nd|rd|th)\s+(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
            normalized_rule_lower,
        )
        if ordinal_match:
            nth = int(ordinal_match.group("nth"))
            weekday = ordinal_match.group("weekday")
            return self._next_nth_weekday(nth, weekday, today)

        for date_format in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(normalized_rule, date_format).date()
            except ValueError:
                continue

        raise Exception(f"Unsupported pickup rule returned by API: '{pickup_rule}'")

    def _fetch_unofficial(self):
        response = requests.get(
            UNOFFICIAL_URL,
            params={"recordID": self._object_id},
            headers=HEADERS,
        )
        response.raise_for_status()

        try:
            json_data = response.json()
        except Exception as e:
            raise Exception(
                f"Invalid response returned from source: {UNOFFICIAL_URL}"
            ) from e

        # Current unofficial endpoint returns nested objects with explicit pickup dates.
        if isinstance(json_data, dict) and any(
            key in json_data for key in ("trash", "recycling", "bulkyWaste")
        ):
            today = datetime.now().date()
            entries = []

            def _first_upcoming_pickup_date(pickups):
                for pickup in pickups or []:
                    pickup_date = (
                        pickup.get("date") if isinstance(pickup, dict) else None
                    )
                    if not pickup_date:
                        continue
                    try:
                        parsed_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
                    except ValueError:
                        continue
                    if parsed_date >= today:
                        return parsed_date

                return None

            trash_data = json_data.get("trash", {})
            trash_date = None
            if isinstance(trash_data, dict):
                next_date = trash_data.get("next", {}).get("date")
                if next_date:
                    try:
                        trash_date = datetime.strptime(next_date, "%Y-%m-%d").date()
                        if trash_date < today:
                            trash_date = None
                    except ValueError:
                        trash_date = None
                if trash_date is None and trash_data.get("day"):
                    trash_date = self._resolve_pickup_date(
                        str(trash_data["day"]), today
                    )

            if trash_date is not None:
                entries.append(
                    Collection(date=trash_date, t="TRASH", icon=ICON_MAP.get("TRASH"))
                )

            recycling_data = json_data.get("recycling", {})
            recycle_date = None
            if isinstance(recycling_data, dict):
                recycle_date = _first_upcoming_pickup_date(
                    recycling_data.get("pickups")
                )
                if recycle_date is None and recycling_data.get("day"):
                    recycle_date = self._resolve_pickup_date(
                        str(recycling_data["day"]), today
                    )

            if recycle_date is not None:
                entries.append(
                    Collection(
                        date=recycle_date,
                        t="RECYCLE",
                        icon=ICON_MAP.get("RECYCLE"),
                    )
                )

            bulky_data = json_data.get("bulkyWaste", {})
            bulky_date = None
            if isinstance(bulky_data, dict):
                bulky_date = _first_upcoming_pickup_date(bulky_data.get("pickups"))
                if bulky_date is None and bulky_data.get("schedule"):
                    bulky_date = self._resolve_pickup_date(
                        str(bulky_data["schedule"]), today
                    )

            if bulky_date is not None:
                entries.append(
                    Collection(date=bulky_date, t="BULKY", icon=ICON_MAP.get("BULKY"))
                )

            if entries:
                return entries

        records = json_data.get("Records")
        if records is None:
            records = json_data.get("records")
        if not records:
            raise Exception(
                "No records found for objectID in unofficial source. Please verify your objectID."
            )

        fields = json_data.get("Fields")
        if fields is None:
            fields = json_data.get("fields", [])

        record = records[0]
        if len(record) != len(fields):
            raise Exception("Invalid record format returned from unofficial source")

        today = datetime.now().date()
        entries = []

        for field, raw_value in zip(fields, record):
            field_name = str(field.get("FieldName", ""))

            if field_name in {"Notice", "Shape"} or not field_name.startswith("Next_"):
                continue

            if raw_value is None:
                continue

            value = str(raw_value).strip()
            if value == "" or value.lower() == "not available":
                continue

            waste_type = field_name.replace("Next_", "").split("_")[0].upper()
            entries.append(
                Collection(
                    date=self._resolve_pickup_date(value, today),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries

    def _fetch_official(self):
        today = datetime.now().date()
        entries = []

        for waste_type, dataset_name in DATASET_BY_TYPE.items():
            field_values = self._fetch_record(
                dataset_name, self._record_ids[waste_type]
            )
            pickup_rule = field_values.get("Pickup_Day", "")

            if not isinstance(pickup_rule, str) or pickup_rule.strip() == "":
                raise Exception(
                    f"Missing Pickup_Day for dataset '{dataset_name}' and Object ID {self._record_ids[waste_type]}"
                )

            entries.append(
                Collection(
                    date=self._resolve_pickup_date(pickup_rule, today),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries

    def fetch(self):
        if self._try_official:
            return self._fetch_official()

        return self._fetch_unofficial()
