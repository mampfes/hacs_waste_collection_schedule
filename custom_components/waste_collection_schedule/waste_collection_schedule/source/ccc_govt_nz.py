import datetime
import requests
import logging

from waste_collection_schedule import Collection


TITLE = "Christchurch City Council"
DESCRIPTION = "Source for Christchurch City Council."
URL = "https://ccc.govt.nz"
TEST_CASES = {"53 Hereford Street": {"address": "53 Hereford Street"}}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycle": "mdi:recycle",
    "Organic": "mdi:leaf",
}

ADDRESS_SUGGEST_URL = "https://opendata.ccc.govt.nz/CCCSearch/rest/address/suggest"
BIN_SERVICE_URL = "https://ccc-data-citizen-api-v1-prod.au-s1.cloudhub.io/api/v1/properties/"
OVERRIDES_URL = "https://ccc.govt.nz/api/kerbsidedateoverrides"

BINS_HEADERS = {
    "client_id": "69f433c880c74c349b0128e9fa1b6a93",
    "client_secret": "139F3D2A83E34AdF98c80566f2eb7212",
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, address:str):
        self._address = address

    def fetch(self) -> list[Collection]:
        entries = []

        # Find the Rating Unit ID by the physical address
        # While a property may have more than one address, bins are allocated by each Rating Unit
        addressQuery = {
            "q": self._address,
            "status": "current",
            "crs": "epsg:4326",
            "limit": 1,
        }

        _LOGGER.debug("Fetching address from %s", ADDRESS_SUGGEST_URL)
        addressResponse = requests.get(ADDRESS_SUGGEST_URL, params=addressQuery)
        _LOGGER.debug("Got address response %s... attempting to JSONify...", addressResponse)
        address = addressResponse.json()
        _LOGGER.debug("Got JSON address %s", address)

        binUrl = BIN_SERVICE_URL + str(address[0]["RatingUnitID"])
        _LOGGER.debug("Fetching bins via RatingUnitID from %s", binUrl)
        binResponse = requests.get(binUrl, headers=BINS_HEADERS)
        _LOGGER.debug("Got bin response %s... attempting to JSONify...", binResponse)
        bins = binResponse.json()
        
        # Deduplicate the Bins in case the Rating Unit has more than one of the same Bin type
        _LOGGER.debug("Deduplicating bins...")
        bins = {each["material"]: each for each in bins["bins"]["collections"]}.values()
        _LOGGER.debug("Deduplication complete")

        # Get the list of Overrides for any special dates
        # It will be an array of these: { ID: 32, Title: "New Year Friday 2024", OriginalDate: "2024-01-05", NewDate: "2024-01-06", Expired: 0 }
        session = requests.Session()
        _LOGGER.debug("Starting session to get visid_incap and incap_ses cookies...")
        session.get(OVERRIDES_URL)
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
            "Accept":"application/json",
            "Host":"ccc.govt.nz",
        }
        _LOGGER.debug("Fetching overrides from %s with required WAF cookies", OVERRIDES_URL)
        print(session.cookies)
        overridesResponse = session.get(OVERRIDES_URL, headers=headers)
        _LOGGER.debug("Got overrides response %s... attempting to JSONify...", overridesResponse)
        overrides = overridesResponse.json()

        _LOGGER.debug("Processing overrides...")
        for bin in bins:
            for override in overrides:
                if override["OriginalDate"] == bin["next_planned_date_app"]:
                    _LOGGER.debug("Processing overrides for %s", override["OriginalDate"])
                    bin["next_planned_date_app"] = override["NewDate"]
        _LOGGER.debug("Overrides processing complete")

        _LOGGER.debug("Processing bins...")
        for bin in bins:
            _LOGGER.debug("Processing bin %s", bin)
            entries.append(
                Collection(
                    date = datetime.datetime.strptime(bin["next_planned_date_app"],"%Y-%m-%d").date(),
                    t = bin["material"],
                    icon = ICON_MAP.get(bin["material"])
                )
            )
        _LOGGER.debug("Bin processing complete. Good to GO! Bin Good?")
        return entries
    
