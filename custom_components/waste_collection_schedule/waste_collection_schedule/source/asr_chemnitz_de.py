import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS
from bs4 import BeautifulSoup

TITLE = "ASR Stadt Chemnitz"
DESCRIPTION = "Source for ASR Stadt Chemnitz."
URL = "https://www.asr-chemnitz.de"
TEST_CASES = {
    "Hübschmannstr. 4": {"street": "Hübschmannstr.", "house_number": "4"},
    "Carl-von-Ossietzky-Str 94": {"street": "Carl-von-Ossietzky-Str", "house_number": 94},
    "Wasserscheide 5 (2204101)": {"street": "Wasserscheide", "house_number": "5", "object_number": "2204101"},
    "Wasserscheide 5 (89251)": {"street": "Wasserscheide", "house_number": "5", "object_number": 89251},
    "Damaschkestraße 36": {"street": "Damaschkestr.", "house_number": "36"},
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Weihnachtsbaum": "mdi:pine-tree",
    "Bio": "mdi:leaf",
    "Pappe, Papier & Kart.": "mdi:package-variant",
    "Leichtstoffverpackungen": "mdi:recycle",
}


API_URL = "https://asc.hausmuell.info/ics/ics.php"


class Source:
    def __init__(self, street: str, house_number: str | int, object_number: str | int = ""):
        self._street: str = street
        self._house_number: str = str(house_number)
        self._object_number: str = str(object_number)
        self._ics = ICS()

    def fetch(self):
        # get hidden_id_egebiet
        args = {
            "input": self._street,
            "ort_id": 0,
            "str_id": 0,
            "input_hnr": self._house_number,
            "url": 2,
            "hidden_kalenderart": "privat",
        }

        r = requests.post("https://asc.hausmuell.info/proxy.php", data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        street_id = soup.find("span").text.strip()
        args["str_id"] = street_id
        args["url"] = 3
        args["input"] = self._house_number

        r = requests.post("https://asc.hausmuell.info/proxy.php", data=args)
        r.raise_for_status()
      
        soup = BeautifulSoup(r.text, "html.parser")
        street_id = soup.find("span").text.strip()
        egebiet_id = soup.find_all("span")[1].text.strip()
        
        
        if egebiet_id == "0":
            if self._object_number == "":
                raise Exception("No object number provided but needed")
            args["input"] = self._object_number
            args["url"] = 7           
            r = requests.post("https://asc.hausmuell.info/proxy.php", data=args)
            r.raise_for_status()           
            soup = BeautifulSoup(r.text, "html.parser")
            egebiet_id = soup.find_all("span")[1].text.strip()
                      
                      
        # get dates
        args = {
            "input_str": self._street,
            "input_hnr": self._house_number,
            "input_objektnr": self._object_number,
            "input_ort": "Ort",
            "hidden_id_ort": 0,
            "hidden_id_ortsteil": 0,
            "hidden_id_egebiet": egebiet_id,
            "hidden_kalenderart": "privat",
            "hidden_send_btn": "ics",
            "hiddenYear": "",
            "showBinsRest": True,
            "showBinsRest_rc": True,
            "showBinsDsd": True,
            "showBinsBio": True,
            "showBinsProb": True,
            "showBinsPapier": True,
            "showBinsXmas": True,
            "showBinsOrganic": True,
        }

        # get json file
        r = requests.post(API_URL, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            bin_type = d[1].replace("Entsorgung:", "").strip()

            entries.append(Collection(
                d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
