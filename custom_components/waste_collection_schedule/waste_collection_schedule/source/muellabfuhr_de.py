from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Müllabfuhr Deutschland"
DESCRIPTION = "Source for Müllabfuhr, Germany"
URL = "https://portal.muellabfuhr-deutschland.de/"
TEST_CASES = {
    "TestcaseI": {
        "client": "Landkreis hildburghausen",
        "city": "Gompertshausen",
    },
    "TestcaseII": {
        "client": "Saalekreis",
        "city": "kabelsketal",
        "district": " Großkugel",
        "street": "Am markt",
    },
    "TestcaseIII": {
        "client": "saalekreis",
        "city": "Kabelsketal",
        "district": "kleinkugel ",
    },
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "gelbe Tonne/Leichtverpackungen": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Biomüll": "mdi:leaf",
}


class Source:
    def __init__(self, client, city, district=None, street=None):
        self._client = client
        self._city = city
        self._district = district
        self._street = street

    def make_request(self, clientid, location_id, endpoint="?includeChildren=true"):
        url = (
            URL
            + "/api-portal/mandators/"
            + clientid
            + "/cal/location/"
            + location_id
            + endpoint
        )
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_data(self, clientid, prev_id, name_search, not_found_message):
        elements = self.make_request(clientid, prev_id)
        for element in elements["children"]:
            if name_search.lower().strip() == element["name"].lower().strip():
                return element["id"], element.get("isFinal")
        raise Exception(not_found_message)

    def fetch(self):
        clientid = None
        configid = None
        cityid = None
        districtid = None
        streetid = None
        cisFinal = False
        disFinal = False

        # get Client
        url = URL + "/api-portal/mandators"
        r = requests.get(url)
        r.raise_for_status()
        clients = r.json()

        for client in clients:
            if self._client.lower().strip() == client["name"].lower().strip():
                clientid = client["id"]

        if clientid is None:
            raise Exception("Sorry, no client found")

        # get client config
        url = URL + "api-portal/mandators/" + clientid + "/config"
        r = requests.get(url)
        r.raise_for_status()
        config = r.json()

        configid = config["calendarRootLocationId"]

        # get city list
        cityid, cisFinal = self.get_data(
            clientid, configid, self._city, "Sorry, no city found"
        )

        # get district list(optional)
        districtid = cityid
        if self._district is not None and not cisFinal:
            districtid, disFinal = self.get_data(
                clientid, cityid, self._district, "Sorry, no district found"
            )

        # get street list(optional)
        streetid = districtid
        if self._street is not None and not disFinal:
            streetid, _ = self.get_data(
                clientid, districtid, self._street, "Sorry, no street found"
            )

        # get pickups
        pickups = self.make_request(clientid, streetid, endpoint="/pickups")

        entries = []
        for pickup in pickups:
            d = datetime.strptime(pickup["date"], "%Y-%m-%d").date()
            entries.append(
                Collection(
                    d,
                    pickup["fraction"]["name"],
                    icon=ICON_MAP.get(pickup["fraction"]["name"]),
                )
            )

        return entries
