import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "AHE Ennepe-Ruhr-Kreis"
TITLE_LANG = "de"
DESCRIPTION = "Source for AHE Ennepe-Ruhr-Kreis."
DESCRIPTION_LANG = "de"
URL = "https://ahe.de"
TEST_CASES = {
    "58300 Ahornstraße 1": {
        "postcode": "58300",
        "street": "Ahornstraße",
        "house_number": 1,
    },
    "58313 Alte Straße 1": {
        "postcode": 58313,
        "street": "alte STraße",
        "house_number": "1",
    },
}


ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find the parameter of your address using [https://ahe.atino.net/pickup-dates](https://ahe.atino.net/pickup-dates) and write them exactly like on the web page."
}


API_URL = "https://ahe.atino.net/{search}"
SEARCH_API_URL = API_URL.format(search="search/{search}")


class Source:
    def __init__(self, postcode: str | int, street: str, house_number: str | int):
        self._plz: str = str(postcode).strip()
        self._strasse: str = street
        self._hnr: str | int = house_number
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        r = s.get(API_URL.format(search="pickup-dates"))
        r.raise_for_status()

        token = BeautifulSoup(r.text, "html.parser").find(
            "input", {"name": "pickup_date[_token]"}
        )["value"]

        r = s.get(
            SEARCH_API_URL.format(search="postalcode"),
            params={
                "q": self._plz,
            },
        )
        r.raise_for_status()

        post_id = None
        for entry in r.json():
            if entry["text"] == self._plz.replace(" ", ""):
                post_id = entry["id"]
                break
        if post_id is None:
            raise SourceArgumentNotFound("postcode", self._plz)

        r = s.get(
            SEARCH_API_URL.format(search="city"),
            params={
                "postalCode": self._plz,
            },
        )
        r.raise_for_status()

        data = r.json()
        if "id" not in data:
            raise SourceArgumentNotFound("postcode", self._plz)

        city_id = data["id"]

        r = s.get(
            SEARCH_API_URL.format(search="street"),
            params={"cityId": city_id, "q": self._strasse},
        )
        r.raise_for_status()

        street_id = None
        data = r.json()
        for entry in data:
            if (
                entry["name"].replace(" ", "").replace(" ", "").strip().lower()
                == self._strasse.replace(" ", "").replace(" ", "").strip().lower()
            ):
                street_id = entry["id"]
                break
        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._strasse, (entry["name"] for entry in data)
            )

        data = {
            "pickup_date[postalCode]": post_id,
            "fake_pickup_date[postalCode]": post_id,
            "pickup_date[street]": street_id,
            "pickup_date[houseNumber]": self._hnr,
            "pickup_date[format]": "1",
            "pickup_date[submit]": "",
            "pickup_date[_token]": token,
        }
        r = s.post(API_URL.format(search="pickup-dates"), data=data)
        r.raise_for_status()
        if "Es wurden keine Termine gefunden." in r.text:
            raise Exception(
                "No dates found for provided addresses please check https://ahe.atino.net/pickup-dates"
            )

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], icon=ICON_MAP.get(d[1])))
        return entries
