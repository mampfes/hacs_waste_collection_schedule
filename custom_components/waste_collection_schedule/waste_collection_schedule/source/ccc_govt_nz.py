import datetime

import requests
from waste_collection_schedule import Collection

# Updated to work around SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error using method discussed in
# https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
import ssl
import urllib3

TITLE = "Christchurch City Council"
DESCRIPTION = "Source for Christchurch City Council."
URL = "https://ccc.govt.nz/services/rubbish-and-recycling/collections"
TEST_CASES = {"53 Hereford Street": {"address": "53 Hereford Street"}}

# Additional code snippet to work around SSL issue
class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session
# End SSL issue code snippet

class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        entries = []

        # Find the Rating Unit ID by the physical address
        # While a property may have more than one address, bins are allocated by each Rating Unit
        addressQuery = {
            "q": self._address,
            "status": "current",
            "crs": "epsg:4326",
            "limit": 1,
        }

        # Updated request using SSL code snippet
        r = get_legacy_session().get("https://opendata.ccc.govt.nz/CCCSearch/rest/address/suggest",
            params=addressQuery,
            # verify=False,
        )

        # Original request code
        # r = requests.get(
        #     "https://opendata.ccc.govt.nz/CCCSearch/rest/address/suggest",
        #     params=addressQuery,
        # )
        address = r.json()

        # Find the Bin service by Rating Unit ID
        binsHeaders = {
            "client_id": "69f433c880c74c349b0128e9fa1b6a93",
            "client_secret": "139F3D2A83E34AdF98c80566f2eb7212"
        }

        # Updated request using SSL code snippet
        r = get_legacy_session().get("https://ccc-data-citizen-api-v1-prod.au-s1.cloudhub.io/api/v1/properties/" + str(address[0]["RatingUnitID"]),
            headers=binsHeaders
            # verify=False,
        )

        # Original request code
        # r = requests.get(
        #     "https://ccc-data-citizen-api-v1-prod.au-s1.cloudhub.io/api/v1/properties/" + str(address[0]["RatingUnitID"]),
        #     headers=binsHeaders
        # )
        bins = r.json()
        
        # Deduplicate the Bins in case the Rating Unit has more than one of the same Bin type
        bins = {each["material"]: each for each in bins["bins"]["collections"]}.values()

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
