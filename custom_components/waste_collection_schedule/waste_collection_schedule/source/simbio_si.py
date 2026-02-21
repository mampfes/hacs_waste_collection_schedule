from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Simbio"
DESCRIPTION = "Source for Simbio."
URL = "https://www.simbio.si/"
TEST_CASES = {
    "Ljubljanska cesta 1 A": {"street": "Ljubljanska cesta", "house_number": "1 A"},
}

BIN_TYPES = {
    "mko": "Mesani",
    "bio": "Bioloski",
    "emb": "Embalaza",
}
ICON_MAP = {
    "mko": "mdi:trash-can",
    "bio": "mdi:leaf",
    "emb": "mdi:recycle",
}

BASE_URL = "https://www.simbio.si/sl/moj-dan-odvoza-odpadkov"


class Source:
    def __init__(self, street: str, house_number: str | int):
        self._street: str = street
        self._house_number: str = str(house_number)

    def fetch(self) -> list[Collection]:
        data = {
            "query": self._street + " " + self._house_number,
            "action": "simbioOdvozOdpadkov",
        }
        r = requests.post(BASE_URL, data=data)
        r.raise_for_status()
        if r.text == "null" or not r.json():
            raise Exception("Invalid address")

        entries = []
        response_data = r.json()

        if isinstance(response_data, list) and response_data:
            waste_data = response_data[0]
            for key, value in waste_data.items():
                if not key.startswith("next_"):
                    continue
                bin_name = key.split("_")[1]
                bin_type, icon = BIN_TYPES.get(bin_name, bin_name), ICON_MAP.get(
                    bin_name
                )

                mes_date = self.get_date(value)
                if mes_date is not None:
                    entries.append(Collection(date=mes_date, t=bin_type, icon=icon))
        else:
            raise Exception("Invalid response from server")
        return entries

    def get_date(self, date_info):
        parsed_date = date_info.split(",")

        if isinstance(parsed_date, list) and len(parsed_date) == 1:
            return None
        else:
            date_obj = datetime.strptime(parsed_date[1].strip(), "%d. %m. %Y")
            return date_obj.date()
