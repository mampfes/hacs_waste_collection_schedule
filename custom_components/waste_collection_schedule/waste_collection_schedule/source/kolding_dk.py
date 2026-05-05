from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Kolding Kommune"
DESCRIPTION = "Source for Kolding Kommune waste collection schedule"
URL = "https://kolding.dk"
TEST_CASES = {
    "TestCase1": {
        "id": "00007b8d-0002-0001-4164-647265737320",
    },
}

ICON_MAP = {
    "REST-MAD": "mdi:trash-can",
    "PAP-PAPIR": "mdi:newspaper",
    "PLAST-GLAS-METAL": "mdi:recycle",
    "TEKSTIL": "mdi:recycle",
    "MADAFFALD": "mdi:food",
    "RESTAFFALD": "mdi:trash-can",
    "FARLIGT-AFFALD": "mdi:biohazard",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to https://kolding.infovision.dk/public/selectaddress and search for your address. Your ID is in the URL, e.g. `00007b8d-0002-0001-4164-647265737320`.",
}


class Source:
    def __init__(self, id: str):
        self._id = id
        self._api_url = f"https://koldingivapi.infovision.dk/api/publiccitizen/container/address/active/{self._id}"

    def fetch(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "publicaccesstoken": "__NetDialogCitizenPublicAccessToken__",
            "User-Agent": "Mozilla/5.0",
        }

        response = requests.get(self._api_url, headers=headers)
        response.raise_for_status()
        containers = response.json()

        entries = []

        for container in containers:
            name = container.get("containerType", {}).get(
                "description", "Ukendt beholder"
            )
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
            elif "drikkekarton" in lower_name and "plast" in lower_name:
                fraktion = "Plast og mad- og drikkekartoner"
                icon = ICON_MAP.get("PLAST-GLAS-METAL")
            elif "metal" in lower_name and "papir" in lower_name:
                fraktion = "Pap/papir og glas/metal"
                icon = ICON_MAP.get("PLAST-GLAS-METAL")
            elif "madaffald" in lower_name or (
                "mad" in lower_name and "rest" not in lower_name
            ):
                fraktion = "Madaffald"
                icon = ICON_MAP.get("MADAFFALD")
            elif "restaffald" in lower_name or (
                "rest" in lower_name and "mad" not in lower_name
            ):
                fraktion = "Restaffald"
                icon = ICON_MAP.get("RESTAFFALD")
            elif "papir" in lower_name or "pap" in lower_name:
                fraktion = "Papir"
                icon = ICON_MAP.get("PAP-PAPIR")
            elif "plast" in lower_name or "glas" in lower_name or "metal" in lower_name:
                fraktion = "Plast/Glas/Metal"
                icon = ICON_MAP.get("PLAST-GLAS-METAL")
            elif "tekstil" in lower_name:
                fraktion = "Tekstilaffaldspose"
                icon = ICON_MAP.get("TEKSTIL")

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
