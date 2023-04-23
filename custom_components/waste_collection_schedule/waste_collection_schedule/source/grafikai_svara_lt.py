import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Kauno švara"
DESCRIPTION = 'Source for UAB "Kauno švara".'
URL = "https://grafikai.svara.lt"
TEST_CASES = {
    "Demokratų g. 7, Kaunas": {
        "region": "Kauno m. sav.",
        "street": "Demokratų g.",
        "house_number": "7",
        "waste_object_ids": [101358, 100858, 100860],
    },
    "Alytaus g. 2, Išlaužo k., Išlaužo sen. Prienų r. sav.": {
        "region": "Prienų r. sav.",
        "street": "Alytaus g.",
        "house_number": "2",
        "district": "Išlaužo sen.",
    },
}

ICON_MAP = {
    "mišrių atliekų": "mdi:trash-can",
    "antrinių žaliavų (popierius/plastikas)": "mdi:recycle",
    "antrinių žaliavų (stiklas)": "mdi:glass-fragile",
    "žaliųjų atliekų": "mdi:leaf",
}


class Source:
    API_URL = "https://grafikai.svara.lt/api/"

    def __init__(
        self, region, street, house_number, district=None, waste_object_ids=None
    ):
        if waste_object_ids is None:
            waste_object_ids = []
        self._region = region
        self._street = street
        self._house_number = house_number
        self._district = district
        self._waste_object_ids = waste_object_ids

    def fetch(self):

        address_query = {
            "pageSize": 20,
            "pageIndex": 0,
            "address": self._street,
            "region": self._region,
            "houseNumber": self._house_number,
            "subDistrict": self._district,
            "matchHouseNumber": "true",
        }
        r = requests.get(
            self.API_URL + "contracts",
            params=address_query,
        )

        data = json.loads(r.text)

        self.check_for_error_status(data)

        entries = []

        for collection in data["data"]:
            try:
                type = collection["descriptionPlural"].casefold()
                if self.check_if_waste_object_defined(collection["wasteObjectId"]):
                    waste_object_query = {"wasteObjectId": collection["wasteObjectId"]}

                    rwo = requests.get(
                        self.API_URL + "schedule",
                        params=waste_object_query,
                    )
                    data_waste_object = json.loads(rwo.text)
                    self.check_for_error_status(data_waste_object)

                    for collection_waste_object in data_waste_object:
                        entries.append(
                            Collection(
                                date=datetime.strptime(
                                    collection_waste_object["date"], "%Y-%m-%dT%H:%M:%S"
                                ).date(),
                                t=collection["descriptionFmt"].title(),
                                icon=ICON_MAP.get(type),
                            )
                        )
            except ValueError:
                pass  # ignore date conversion failure for not scheduled collections

        return entries

    def check_if_waste_object_defined(self, waste_object_id):
        if len(self._waste_object_ids) <= 0:
            return True
        if waste_object_id in self._waste_object_ids:
            return True
        return False

    def check_for_error_status(self, collection):
        if "status" in collection:
            raise Exception(
                "Error: failed to fetch get data, got status: {}".format(
                    collection["status"]
                )
            )
