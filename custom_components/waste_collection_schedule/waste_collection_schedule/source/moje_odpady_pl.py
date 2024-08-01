from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "App Moje Odpady"
DESCRIPTION = "Source for App Moje Odpady."
URL = "https://moje-odpady.pl/"
TEST_CASES = {
    "Aleksandr\u00f3w woj. \u015bl\u0105skie": {
        "city": "Aleksandr\u00f3w",
        "voivodeship": "woj. \u015bl\u0105skie",
    },
    "with address and house_number": {
        "city": "BASZKÓWKA",
        "voivodeship": "woj. mazowieckie",
        "address": "ANTONÓWKI",
        "house_number": "Pozosta\u0142e",
    },
    "english bin types": {
        "city": "Marcin\u00f3w",
        "voivodeship": "woj. \u0142\u00f3dzkie",
        "english": True,
    },
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


API_URL = "https://waste24.net/client/api/mywaste/v2/location_cities.php"


def make_comparable(text: str) -> str:
    return text.lower().replace(" ", "").replace(".", "")


class Source:
    def __init__(
        self,
        city: str,
        voivodeship: str | None = None,
        address: str | None = None,
        house_number: str | None = None,
        english: bool = False,
    ):
        self._city: str = make_comparable(city)
        self._voivodeship: str | None = (
            make_comparable(voivodeship) if voivodeship else None
        )
        self._address: str | None = make_comparable(address) if address else None
        self._house_number: str | None = (
            make_comparable(house_number) if house_number else None
        )
        self._english: bool = english

        self._org_number: int | None = None
        self._real_city_name: str | None = None
        self._real_address: str | None = None
        self._real_house_number: str | None = None

    def _fetch_house_number(self):
        payload = {
            "org": self._org_number,
            "city": self._real_city_name,
            "address": self._real_address,
        }
        r = requests.post(
            "https://waste24.net/client/api/mywaste/v2/location_addresses_nr.php",
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        if len(data) == 0:
            return
        if len(data) == 1:
            self._real_house_number = data[0]["addressNr"]
            return

        if self._house_number is None:
            raise ValueError(
                f"House number is required for this address, use one of {[a['nr'] for a in data]}"
            )

        self._real_house_number = None
        for house_number in data:
            if make_comparable(house_number["addressNr"]) == self._house_number:
                self._real_house_number = house_number["addressNr"]
                break

        if self._real_house_number is None:
            raise ValueError(
                f"House number {self._house_number} not found, use one of {[a['nr'] for a in data]}"
            )

    def _fetch_address(self):
        payload = {"org": self._org_number, "city": self._real_city_name}
        r = requests.post(
            "https://waste24.net/client/api/mywaste/v2/location_addresses.php",
            json=payload,
        )
        r.raise_for_status()

        data = r.json()
        if self._address is None:
            raise ValueError(
                f"Address is required for this city, use one of {[a['addressName'] for a in data]}"
            )

        countOfChilds = None

        for address in data:
            if make_comparable(address["addressName"]) == self._address:
                self._real_address = address["addressName"]
                break
        if self._real_address is None:
            raise ValueError(
                f"Address {self._address} not found, use one of {[a['addressName'] for a in data]}"
            )

        if countOfChilds:
            self._fetch_house_number()

    def fetch_area(self):
        r = requests.post(
            "https://waste24.net/client/api/mywaste/v2/location_cities.php"
        )
        r.raise_for_status()

        data = r.json()
        city_matches = []

        for city in data:
            if make_comparable(city["cityName"]) == self._city:
                city_matches.append(city)

        if not city_matches:
            raise ValueError(
                f"City {self._city} not found, use one of {[c['cityName'] for c in data]}"
            )

        self._org_number = None
        self._real_city_name = None
        countOfChilds = None

        if len(city_matches) == 1:
            self._org_number = city_matches[0]["org"]
            self._real_city_name = city_matches[0]["cityName"]
            countOfChilds = city_matches[0]["countOfChilds"]
        else:
            if self._voivodeship is None:
                raise ValueError(
                    f"Multiple cities found, specify voivodeship, use one of {[c['voivodeship'] for c in city_matches]}"
                )
            for city in city_matches:
                if make_comparable(city["voivodeship"]) == self._voivodeship:
                    self._org_number = city["org"]
                    self._real_city_name = city["cityName"]
                    countOfChilds = city["countOfChilds"]
                    break
        if self._org_number is None:
            raise ValueError(
                f"City {self._city} in voivodeship {self._voivodeship} not found, use one of {[c['voivodeship'] for c in city_matches]}"
            )

        if countOfChilds:
            self._fetch_address()

    def _get_scheduele(self) -> list[Collection]:
        payload = {
            "org": self._org_number,
            "city": self._real_city_name,
            "address": self._real_address or "",
            "addressNr": self._real_house_number or "",
        }
        r = requests.post(
            "https://waste24.net/client/api/mywaste/v2/schedule_list.php", json=payload
        )
        r.raise_for_status()
        data = r.json()
        print(data)
        entries = []
        for collection in data:
            date_ = datetime.strptime(collection["data"], "%Y-%m-%d").date()
            for containers in collection["containers"]:
                bin_type = containers["containerName"]
                if self._english:
                    bin_type = (
                        containers.get("containerNameEn", bin_type).strip() or bin_type
                    )
                entries.append(Collection(date_, bin_type, ICON_MAP.get(bin_type)))
        return entries

    def fetch(self) -> list[Collection]:
        fresh_params = False
        if self._org_number is None:
            self.fetch_area()
        try:
            return self._get_scheduele()
        except Exception:
            if fresh_params:
                raise
            fresh_params = True
            self.fetch_area()
            return self._get_scheduele()
