import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "Perth and Kinross Council"
DESCRIPTION = "Source for Perth and Kinross Council, UK."
URL = "https://www.pkc.gov.uk"
TEST_CASES = {
    "7 St Marys Drive, Perth, PH2 7BY": {"uprn": "124022910"},
    "10A Crieff Road, Perth, PH1 5AF": {"uprn": 124003157},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN by visiting "
        "https://my.pkc.gov.uk/AchieveForms/?form_uri=sandbox-publish://AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa/AF-Stage-9fa33e2e-4c1b-4963-babf-4348ab8154bc/definition.json "
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

BASE_URL = "https://my.pkc.gov.uk"
INITIAL_URL = (
    f"{BASE_URL}/AchieveForms/?mode=fill&consentMessage=yes"
    "&form_uri=sandbox-publish://AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa/"
    "AF-Stage-9fa33e2e-4c1b-4963-babf-4348ab8154bc/definition.json"
    "&process=1"
    "&process_uri=sandbox-processes://AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa"
    "&process_id=AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa"
)
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
API_URL = f"{BASE_URL}/apibroker/runLookup"
HOSTNAME = "my.pkc.gov.uk"

LOOKUP_ID = "5c9267cee5efe"

# Maps the raw field names returned by the "Bin collections" lookup to a
# human readable waste type and icon. Which fields are populated depends on
# the collection scheme in place for a given property (e.g. some properties
# get combined food/garden waste, others get separate paper or garden
# collections).
FIELD_MAP: dict[str, tuple[str, Icons]] = {
    "nextGeneralWasteCollectionDate": (
        "Non-recyclable waste (green-lidded bin)",
        Icons.GENERAL_WASTE,
    ),
    "nextGeneralWasteCollectionDate2nd": (
        "Non-recyclable waste (green-lidded bin)",
        Icons.GENERAL_WASTE,
    ),
    "nextBlueCollectionDate": (
        "Paper and cardboard (blue-lidded bin)",
        Icons.PAPER,
    ),
    "nextBlueWasteCollectionDate2nd": (
        "Paper and cardboard (blue-lidded bin)",
        Icons.PAPER,
    ),
    "nextGreyWasteCollectionDate": (
        "Plastic bottles, cans and cartons (grey-lidded bin)",
        Icons.RECYCLING,
    ),
    "nextGreyWasteCollectionDate2nd": (
        "Plastic bottles, cans and cartons (grey-lidded bin)",
        Icons.RECYCLING,
    ),
    "nextGardenandFoodWasteCollectionDate": (
        "Food and garden waste (brown-lidded bin)",
        Icons.ORGANIC,
    ),
    "nextGardenandFoodWasteCollectionDate2nd": (
        "Food and garden waste (brown-lidded bin)",
        Icons.ORGANIC,
    ),
    "nextPaperWasteCollectionDate": (
        "Paper and cardboard",
        Icons.PAPER,
    ),
    "nextPaperWasteCollectionDate2nd": (
        "Paper and cardboard",
        Icons.PAPER,
    ),
    "nextGardenWasteCollectionDate": (
        "Garden waste",
        Icons.GARDEN,
    ),
    "nextGardenWasteCollectionDate2nd": (
        "Garden waste",
        Icons.GARDEN,
    ),
    "nextCommunalFoodWasteCollectionDate": (
        "Communal food waste",
        Icons.BIO_KITCHEN,
    ),
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        sid = init_session(session, INITIAL_URL, AUTH_URL, HOSTNAME)

        result = run_lookup(
            session,
            API_URL,
            sid,
            LOOKUP_ID,
            {"Bin collections": {"propertyUPRNQuery": {"value": self._uprn}}},
        )

        rows = result.get("integration", {}).get("transformed", {}).get("rows_data")
        if not isinstance(rows, dict) or not rows:
            raise SourceArgumentNotFound("uprn", self._uprn)

        row = rows.get("0", {})
        if not row or str(row.get("returnedUPRN", "")).strip().lower() in (
            "",
            "false",
        ):
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries = []
        for field, (waste_type, icon) in FIELD_MAP.items():
            date_str = str(row.get(field, "")).strip()
            if not date_str:
                continue
            try:
                collection_date = datetime.datetime.strptime(
                    date_str, "%d/%m/%Y"
                ).date()
            except ValueError:
                continue
            entries.append(Collection(date=collection_date, t=waste_type, icon=icon))

        if not entries:
            raise SourceArgumentNotFound("uprn", self._uprn)

        return entries
