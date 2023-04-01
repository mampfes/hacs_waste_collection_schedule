import re
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Kommunalservice Landkreis Börde AöR"
DESCRIPTION = "Source for KS Börde."
URL = "https://ks-boerde.de"
COUNTRY = "de"
TEST_CASES = {
    "Rathaus": {
        "village": "Irxleben",
        "street": "Bördestraße",
        "house_number": "8",
    },
    "Grundschule": {
        "village": "Bebertal (Eiche/Hüsig)",
        "street": "Am Drei",
        "house_number": "11",
    },
    "KS Börde": {
        "village": "Wolmirstedt",
        "street": "Schwimmbadstraße",
        "house_number": "2a",
    },
}

DATA_URL = "https://www.ks-boerde.de/_aturis/eko/proxy.php"
CALENDAR_URL = "https://boerde.hausmuell.info/ics/ics.php"
ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Leichtverpackungen": "mdi:recycle",
    "Papier, Pappe, Karton": "mdi:package-variant",
    "Schadstoffmobil": "mdi:biohazard",
}


class Source:
    def __init__(
        self, village: str, street: str, house_number: str
    ):
        self._village = village
        self._street = street
        self._house_number = house_number
        self._ics = ICS()

    def get_calendar(self, village: int, street: int, house_number: int, area: int):
        post_data = {
            "input_ort": "",
            "input_ortsteil": "Ortsteil",
            "input_str": "",
            "input_hnr": 0,
            "hidden_id_ort": village,
            "hidden_id_ortsteil": village,
            "hidden_id_str": street,
            "hidden_id_hnr": house_number,
            "hidden_id_egebiet": area,
            "hidden_kalenderart": "privat",
            "hidden_send_btn": "ics",
            "hidden_last_field": "input_zusatz",
            "hidden_checkzusatz": "",
            "hiddenAllOrganicWaste": 0,
            "hiddenCollectablesFraktion": "",
            "hiddenYear": "",
            "hiddenView": "",
        }
        # get calendar from ks-boerde
        ics = requests.post(CALENDAR_URL, data=post_data).text
        # convert text into ICS object
        return self._ics.convert(ics)

    def get_from_proxy(self, village: int = 0, street: int = 0, input: str = ""):
        post_data = {
            "input": input,
            "ort_id": village,
            "str_id": street,
            "hidden_kalenderart": "privat",
            "url": 0 if village == 0 else 2 if street == 0 else 3,
            "server": 0
        }
        data = requests.post(DATA_URL, data=post_data).text
        data = re.findall("<li id = '.*?_\d+'onClick='get_value\(\".*?\",\d+,\d+\)'>" +
                          "<span style = 'display:none;'>(\d+)</span>" +
                          "<span style = 'display:none;'>(\d+)</span>" +
                          "<span>(.*?)</span>" +
                          "</li>", data)
        return [data[0][0], data[0][1]]

    def get_ids(self):
        [village_id, _] = self.get_from_proxy(input=self._village)
        [street_id, _] = self.get_from_proxy(
            village=village_id, input=self._street)
        [house_number_id, area_id] = self.get_from_proxy(
            village=village_id, street=street_id, input=self._house_number)
        return [village_id, street_id, house_number_id, area_id]

    def fetch(self):
        [village_id, street_id, house_number_id, area_id] = self.get_ids()
        dates = self.get_calendar(village_id, street_id,
                                  house_number_id, area_id)

        entries = []
        for d in dates:
            entries.append(Collection(
                date=d[0], t=d[1], icon=ICON_MAP.get(d[1])))
        return entries
