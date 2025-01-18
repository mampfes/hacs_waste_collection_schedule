import requests
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Simbio"
DESCRIPTION = "Source for Simbio."
URL = "https://www.simbio.si/"
TEST_CASES = {
    "Ljubljanska cesta 1 A": {"street": "Ljubljanska cesta", "house_number": '1 A'},
}

BIN_TYPES = {
    "M": "Mesani",
    "B": "Bioloski",
    "E": "Embalaza",
}
ICON_MAP = {
    "M": "mdi:trash-can",
    "B": "mdi:leaf",
    "E": "mdi:recycle",
}

BASE_URL = "https://www.simbio.si/sl/moj-dan-odvoza-odpadkov"


class Source:
    def __init__(self, street: str, house_number: str | int):
        self._street: str = street
        self._house_number: str | int = house_number

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

        if (isinstance(response_data, list) and response_data):
            waste_data = response_data[0]

            mes_date = self.get_date(waste_data.get("next_mko"))
            if not mes_date is None:
                bin_type = BIN_TYPES.get("M", "M")
                icon = ICON_MAP.get("M")
                entries.append(Collection(date=mes_date, t=bin_type, icon=icon))

            emb_date = self.get_date(waste_data.get("next_emb"))
            if not emb_date is None:
                bin_type = BIN_TYPES.get("E", "E")
                icon = ICON_MAP.get("E")
                entries.append(Collection(date=emb_date, t=bin_type, icon=icon))

            bio_date = self.get_date(waste_data.get("next_bio"))
            if not bio_date is None:
                bin_type = BIN_TYPES.get("B", "B")
                icon = ICON_MAP.get("B")
                entries.append(Collection(date=bio_date, t=bin_type, icon=icon))

        return entries

    def get_date(self, date_info):
        parsed_date = date_info.split(",")

        if isinstance(parsed_date, list) and len(parsed_date) == 1:
            return None
        else:
            date_obj = datetime.strptime(parsed_date[1].strip(), "%d. %m. %Y")
            return date_obj.date()