from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Kalundborg Kommune"
DESCRIPTION = "Source for Kalundborg Kommune waste collection schedule"
URL = "https://kalundborg.dk"
TEST_CASES = {
    "TestCase1": {
        "id": "00006ac8-0002-0001-4164-647265737320",
    },
    "TestCase2": {
        "id": "00008d18-0002-0001-4164-647265737320",
    },
    "TestCase3": {
        "id": "00006643-0002-0001-4164-647265737320",
    },
}

ICON_MAP = {
    "REST-MAD": "mdi:trash-can",
    "PAP-PAPIR": "mdi:newspaper", 
    "PLAST-GLAS-METAL": "mdi:recycle",
    "MADAFFALD": "mdi:food",
    "RESTAFFALD": "mdi:trash-can",
    "FARLIGT-AFFALD": "mdi:biohazard",
}


class Source:
    def __init__(self, id: str):
        self._id = id
        self._api_url = f"https://kalundborgivapi.infovision.dk/api/publiccitizen/container/address/active/{self._id}"

    def fetch(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "publicaccesstoken": "__NetDialogCitizenPublicAccessToken__",
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(self._api_url, headers=headers)
        response.raise_for_status()
        containers = response.json()

        entries = []

        for container in containers:
            fraction = container.get("containerType", {}).get("fraction", {}).get("description", "Ukendt")
            name = container.get("containerType", {}).get("description", "Ukendt beholder")
            collect_dates = container.get("collectDates", [])

            # Renodjurs-style matching logic - most specific first
            lower_name = name.lower()
            fraktion = "Ukendt"
            icon = None
            
            if "farligt affald" in lower_name or "miljøkasse" in lower_name:
                fraktion = "Farligt affald"
                icon = ICON_MAP.get("FARLIGT-AFFALD")
            elif "rest" in lower_name and "mad" in lower_name:
                fraktion = "Rest- og Madaffald"
                icon = ICON_MAP.get("REST-MAD")
            elif ("papir" in lower_name or "pap" in lower_name) and ("metal" in lower_name and "plast" in lower_name):
                fraktion = "Blandet genanvendelse"  # Mixed recycling
                icon = ICON_MAP.get("PLAST-GLAS-METAL")
            elif "papir" in lower_name or "pap" in lower_name:
                fraktion = "Pap- og Papiraffald"
                icon = ICON_MAP.get("PAP-PAPIR")
            elif "metal" in lower_name and "plast" in lower_name:
                fraktion = "Plast, Glas og Metalaffald"
                icon = ICON_MAP.get("PLAST-GLAS-METAL")
            elif "mad" in lower_name:
                fraktion = "Madaffald"
                icon = ICON_MAP.get("MADAFFALD")
            elif "rest" in lower_name:
                fraktion = "Restaffald"
                icon = ICON_MAP.get("RESTAFFALD")

            for date_int in collect_dates:
                date_str = str(date_int)
                pickup_date = datetime.strptime(date_str, "%Y%m%d").date()
                
                entries.append(
                    Collection(
                        date=pickup_date,
                        t=fraktion,
                        icon=icon,
                    )
                )

        return entries
