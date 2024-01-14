import datetime

import requests
from waste_collection_schedule import Collection

# Include work around for SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error
from waste_collection_schedule.service.SSLError import get_legacy_session


TITLE = "Christchurch City Council"
DESCRIPTION = "Source for Christchurch City Council."
URL = "https://ccc.govt.nz"
TEST_CASES = {"53 Hereford Street": {"address": "53 Hereford Street"}}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):

        s = get_legacy_session()

        entries = []

        # Find the Rating Unit ID by the physical address
        # While a property may have more than one address, bins are allocated by each Rating Unit
        addressQuery = {
            "q": self._address,
            "status": "current",
            "crs": "epsg:4326",
            "limit": 1,
        }

        r = s.get("https://opendata.ccc.govt.nz/CCCSearch/rest/address/suggest",
            params=addressQuery,
            # verify=False,
        )
        address = r.json()

        # Find the Bin service by Rating Unit ID
        binsHeaders = {
            "client_id": "69f433c880c74c349b0128e9fa1b6a93",
            "client_secret": "139F3D2A83E34AdF98c80566f2eb7212"
        }

        # Updated request using SSL code snippet
        r = s.get("https://ccc-data-citizen-api-v1-prod.au-s1.cloudhub.io/api/v1/properties/" + str(address[0]["RatingUnitID"]),
            headers=binsHeaders
            # verify=False,
        )
        bins = r.json()
        
        # Deduplicate the Bins in case the Rating Unit has more than one of the same Bin type
        bins = {each["material"]: each for each in bins["bins"]["collections"]}.values()

        # Get the list of Overrides for any special dates
        # It will be an array of these: { ID: 32, Title: "New Year Friday 2024", OriginalDate: "2024-01-05", NewDate: "2024-01-06", Expired: 0 }
        overrides = requests.get("https://ccc.govt.nz/api/kerbsidedateoverrides").json()

        # Process each Override
        for bin in bins:
            for override in overrides:
                if override["OriginalDate"] == bin["next_planned_date_app"]:
                    bin["next_planned_date_app"] = override["NewDate"]

        # Process each Bin
        for bin in bins:
            entries.append(
                Collection(
                    datetime.datetime.strptime(
                        bin["next_planned_date_app"], "%Y-%m-%d"
                    ).date(),
                    bin["material"],
                )
            )

        return entries
