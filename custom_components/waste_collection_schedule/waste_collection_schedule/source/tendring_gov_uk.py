from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "Tendring District Council"
DESCRIPTION = "Source for Tendring District Council, Essex, UK."
URL = "https://www.tendringdc.gov.uk"
TEST_CASES = {
    "1 Queens Road, Clacton-on-Sea": {"uprn": "100090613962"},
    "18 High Street, Manningtree": {"uprn": 100091459763},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN by visiting "
        "https://tendring-self.achieveservice.com/en/service/Rubbish_and_recycling_collection_days "
        "and searching for your address. Your UPRN can also be found at "
        "https://www.findmyaddress.co.uk/."
    )
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "UPRN",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) for your address.",
    }
}
COUNTRY = "uk"

BASE_URL = "https://tendring-self.achieveservice.com"
SERVICE_URL = f"{BASE_URL}/en/service/Rubbish_and_recycling_collection_days"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
API_URL = f"{BASE_URL}/apibroker/runLookup"
HOSTNAME = "tendring-self.achieveservice.com"

LOOKUP_COLLECTIONS = "6347acbadc425"

ICON_MAP = {
    "residual": Icons.GENERAL_WASTE,
    "green": Icons.RECYCLING,
    "red": Icons.RECYCLING,
    "food": Icons.BIO_KITCHEN,
    "garden": Icons.GARDEN,
}

# (api_field, waste_type_label, icon_key, conditional_field)
# conditional_field: if set, skip this waste type if the field value is falsy
COLLECTION_FIELDS = [
    ("nextResidualCollection", "Residual waste", "residual", None),
    ("nextGreenCollection", "Green recycling box", "green", None),
    ("nextRedCollection", "Red recycling box", "red", None),
    ("nextFoodCollection", "Food waste", "food", "eligibleFoodCollection"),
    ("nextGardenCollection", "Garden waste", "garden", "activeGardenCollection"),
]


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        sid = init_session(
            session,
            SERVICE_URL,
            AUTH_URL,
            HOSTNAME,
        )
        result = run_lookup(
            session,
            API_URL,
            sid,
            LOOKUP_COLLECTIONS,
            {"Address": {"selectedUPRN": {"value": self._uprn}}},
        )

        rows = result.get("integration", {}).get("transformed", {}).get("rows_data", {})
        row = rows.get("0", {}) if isinstance(rows, dict) else (rows[0] if rows else {})

        if not row:
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries = []
        for date_field, waste_type, icon_key, condition_field in COLLECTION_FIELDS:
            # Skip conditional waste types if the service is not active
            # API returns string "True"/"False" for boolean fields
            if condition_field and row.get(condition_field, "").lower() != "true":
                continue

            date_str = row.get(date_field, "").strip()
            if not date_str:
                continue
            try:
                # API returns dates as "DD/MM/YYYY HH:MM:SS"
                collection_date = datetime.strptime(date_str[:10], "%d/%m/%Y").date()
            except ValueError:
                continue
            # Skip sentinel date returned when service has no next collection
            if collection_date.year < 2000:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(icon_key),
                )
            )

        if not entries:
            raise SourceArgumentNotFound("uprn", self._uprn)

        return entries
