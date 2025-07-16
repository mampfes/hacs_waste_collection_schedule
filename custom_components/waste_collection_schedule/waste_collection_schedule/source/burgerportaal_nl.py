import datetime
import logging
from typing import Literal

import requests
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

TITLE = "BurgerPortaal"
DESCRIPTION = "Source for BurgerPortaal."
URL = "https://21burgerportaal.mendixcloud.com/"


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": s["url"],
            "default_params": {"organization": s["organization"]},
        }
        for s in SERVICE_MAP
    ]


TEST_CASES = {
    "Assen": {"organization": "assen", "post_code": "9401LN", "house_number": 6},
    "RMN": {
        "organization": "rmn",
        "post_code": "3437GS",
        "house_number": 2,
        "addition": "A",
    },
}

Organization = Literal["assen", "rmn"]

SERVICE_MAP = [
    {
        "title": "Assen",
        "url": "https://www.assen.nl/",
        "uuid": "138204213565303512",
        "organization": "assen",
    },
    {
        "title": "Reinigingsdienst Midden Nederland",
        "url": "https://www.rmn.nl/",
        "uuid": "138204213564933597",
        "organization": "rmn",
    },
]


def get_service_name_map():
    return {s["organization"]: s["uuid"] for s in SERVICE_MAP}


class Source:
    def __init__(
        self,
        organization: Organization,
        post_code: str,
        house_number: str,
        addition: str = "",
    ):
        self._api_key: str = "AIzaSyA6NkRqJypTfP-cjWzrZNFJzPUbBaGjOdk"
        self._addition: str = addition
        self._post_code: str = post_code
        self._house_number: str = house_number
        self._url: str = (
            "https://europe-west3-burgerportaal-production.cloudfunctions.net"
        )
        self._organization_code: str = get_service_name_map()[organization]
        self._refresh_token: str = ""
        self._id_token: str = ""
        self._address_id: str = ""

    def _set_refresh_token(self):
        res = requests.post(
            f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key={self._api_key}"
        )
        payload = res.json()
        if not payload:
            _LOGGER.error("Unable to fetch refresh token!")
            return

        self._refresh_token = payload["refreshToken"]
        self._id_token = payload["idToken"]

    def _set_id_token(self) -> None:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {"grant_type": "refresh_token", "refresh_token": self._refresh_token}

        res = requests.post(
            f"https://securetoken.googleapis.com/v1/token?key={self._api_key}",
            headers=headers,
            data=data,
        )
        payload = res.json()
        if not payload:
            _LOGGER.error("Unable to fetch ID token!")
            return
        self._id_token = payload["id_token"]

    def _set_address_id(self) -> None:
        headers = {"authorization": self._id_token}

        res = requests.get(
            f"{self._url}/exposed/organisations/{self._organization_code}/address?zipcode={self._post_code}&housenumber={self._house_number}",
            headers=headers,
        )
        payload = res.json()
        if not payload:
            _LOGGER.error("Unable to fetch address!")
            return

        for address in payload:
            if "addition" in address and address["addition"] == self._addition.upper():
                self.address_id = address["addressId"]

        if not self._address_id:
            self._address_id = payload[-1]["addressId"]

    def fetch(self) -> list[Collection]:
        # get refresh token and id token
        if not self._refresh_token:
            self._set_refresh_token()
        else:
            self._set_id_token()

        # get address id
        if not self._address_id:
            self._set_address_id()

        headers = {"authorization": self._id_token}
        res = requests.post(
            f"{self._url}/exposed/organisations/{self._organization_code}/address/{self._address_id}/calendar",
            headers=headers,
        )
        payload = res.json()

        entries: list[Collection] = []

        for item in payload:
            if not item["collectionDate"]:
                continue

            waste_type = item["fraction"].lower()
            if not waste_type:
                continue

            collection = Collection(
                date=datetime.datetime.strptime(
                    item["collectionDate"].split("T")[0], "%Y-%m-%d"
                ),
                t=waste_type,
                icon=item["fraction"].lower(),
            )
            if collection not in entries:
                entries.append(collection)

        return entries
