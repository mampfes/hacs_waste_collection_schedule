from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Apps by imactivate"
DESCRIPTION = "Source for Apps by imactivate."
URL = "https://imactivate.com/"
TEST_CASES = {
    "Leeds: LS6 2SE Leeds sharp mews 2": {
        "postcode": "LS62SE",
        "town": "Leeds",
        "street": "sharp mews",
        "number": 2,
    },
    "Fenland: PE15 8RD March 90 Creek Rd": {
        "postcode": "PE158RD",
        "town": "March",
        "street": "Creek Road",
        "number": "90",
    },
    "Rotherham: S61 4BH 2 Eskdale Rd, Rotherham": {
        "postcode": "S614BH",
        "town": "Rotherham",
        "street": "Eskdale Road",
        "number": 2,
    },
    "Luton: LU2 9DF 23 Marshall Rd": {
        "postcode": "LU2 9DF",
        "town": "Luton",
        "street": "Marshall Rd",
        "number": 23,
    },
}

COUNTRY = "uk"

EXTRA_INFO = [
    {
        "title": "Leeds",
        "url": "https://www.leeds.gov.uk",
        "default_params": {"town": "Leeds"},
    },
    {
        "title": "Fenland",
        "url": "https://www.fenland.gov.uk",
    },
    {
        "title": "Rotherham",
        "url": "https://www.rotherham.gov.uk",
        "default_params": {"town": "Rotherham"},
    },
    {
        "title": "Luton",
        "url": "https://www.luton.gov.uk",
        "default_params": {"town": "Luton"},
    },
]


ICON_MAP = {
    "waste": "mdi:trash-can",
    "black": "mdi:trash-can",
    "pink bin": "mdi:trash-can",
    "residual": "mdi:trash-can",
    "glass": "mdi:bottle-wine",
    "garden": "mdi:leaf",
    "brown": "mdi:leaf",
    "recycling": "mdi:recycle",
    "green": "mdi:recycle",
    "black bin": "mdi:recycle",
    "green bin": "mdi:package-variant-closed",
}


API_URL = "https://bins.azurewebsites.net/api/"


class Source:
    def __init__(self, postcode: str, town: str, street: str, number: str | int):
        self._postcode: str = postcode
        self._town: str = town.lower().replace(" ", "")
        self._street: str = street.lower().replace(" ", "").replace("road", "rd")
        self._number: str = str(number).lower().replace(" ", "")
        self._premises_id: int | None = None
        self._local_authority: str | None = None

    def _retrieve_premise_id(self) -> None:
        r = requests.get(f"{API_URL}getlocation", params={"postcode": self._postcode})
        r.raise_for_status()
        real_post_code: str = r.json()[0]["Postcode"]

        r = requests.get(f"{API_URL}getaddress", params={"postcode": real_post_code})
        r.raise_for_status()

        data = r.json()
        street_matches = []
        for location in data:
            if (
                location["Street"].lower().replace(" ", "").replace("road", "rd")
                == self._street
                and location["Town"].lower().replace(" ", "") == self._town
            ):
                street_matches.append(location)

        if len(street_matches) == 0:
            possibilities = {
                f"street:'{location['Street']}', Town:{location['Town']}'"
                for location in data
            }
            raise ValueError(
                f"No matching street found use one of {', '.join(possibilities)}"
            )
        for location in street_matches:
            number1 = (
                (location["Address1"].strip() + location["Address2"].strip())
                .replace(" ", "")
                .replace("\u0000", "")
                .lower()
            )
            number2 = (
                (location["Address2"].strip() + location["Address1"].strip())
                .replace(" ", "")
                .replace("\u0000", "")
                .lower()
            )
            if number1 == self._number or number2 == self._number:
                self._premises_id = location["PremiseID"]
                self._local_authority = location["LocalAuthority"]
                return

        possibilities = {
            f"number:'{location['Address1']}{location['Address2']}'"
            for location in street_matches
        }
        raise ValueError(
            f"No matching number found use one of {', '.join(possibilities)}"
        )

    def _fetch_premise(self) -> list[Collection]:
        if self._premises_id is None or self._local_authority is None:
            raise ValueError("Premise ID and Local Authority required")

        params: dict[str, str | int] = {
            "premisesid": self._premises_id,
            "localauthority": self._local_authority,
        }

        r = requests.get(
            f"{API_URL}getcollections",
            params=params,
        )
        r.raise_for_status()
        data = r.json()
        entries = []
        for collection in data:
            if "BinType" not in collection or "CollectionDate" not in collection:
                continue
            icon = ICON_MAP.get(collection["BinType"].lower())
            date_str = collection["CollectionDate"]
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            entries.append(Collection(date, collection["BinType"], icon))

        if not entries:
            raise ValueError("No collections found")
        return entries

    def fetch(self) -> list[Collection]:
        try:
            return self._fetch_premise()
        except Exception:
            pass
        self._retrieve_premise_id()
        return self._fetch_premise()
