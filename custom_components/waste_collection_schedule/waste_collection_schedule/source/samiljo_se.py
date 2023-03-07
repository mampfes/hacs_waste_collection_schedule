import datetime
import urllib.parse

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Samverkan Återvinning Miljö (SÅM)"
DESCRIPTION = "Source script for samiljo.se"
URL = "https://www.samiljo.se"

TEST_CASES = {
    "Test1": {"city": "Reftele", "street": "Storgatan 6"},
    "Test2": {"city": "Värnamo", "street": "Västra Kyrkogårdsgatan 2"},
    "Test3": {"city": "Burseryd", "street": "Storgatan 1"},
}

API_URLS = {
    "address_search": "https://webbservice.indecta.se/kunder/sam/kalender/basfiler/laddaadresser.php",
    "collection": "https://webbservice.indecta.se/kunder/sam/kalender/basfiler/onlinekalender.php",
}

ICON_MAP = {
    "HKARL1": "mdi:trash-can",
    "HKARL1-H": "mdi:trash-can",
    "HKARL2": "mdi:recycle",
    "HKARL2-H": "mdi:recycle",
    "HMAT": "mdi:leaf",
    "HMAT-H": "mdi:leaf",
    "HREST": "mdi:trash-can",
    "HREST-H": "mdi:trash-can",
    "HOSORT": "mdi:trash-can",
    "HOSORT-H": "mdi:trash-can",
}

NAME_MAP = {
    "HKARL1": "Fyrfackskärl 1",  # Matavfall, Restavfall, Tidningar & Färgat glas
    "HKARL1-H": "Fyrfackskärl 1 (Helgvecka - hämtningsdagen kan avika)",  # Matavfall, Restavfall, Tidningar & Färgat glas
    "HKARL2": "Fyrfackskärl 2",  # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "HKARL2-H": "Fyrfackskärl 2 (Helgvecka - hämtningsdagen kan avika)",  # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "HMAT": "Matavfall",
    "HMAT-H": "Matavfall (Helgvecka - hämtningsdagen kan avika)",
    "HREST": "Restavfall",
    "HREST-H": "Restavfall (Helgvecka - hämtningsdagen kan avika)",
    "HOSORT": "Blandat Mat- och Restavfall",
    "HOSORT-H": "Blandat Mat- och Restavfall (Helgvecka - hämtningsdagen kan avika)",
}

MONTH_MAP = {
    "Januari": 1,
    "Februari": 2,
    "Mars": 3,
    "April": 4,
    "Maj": 5,
    "Juni": 6,
    "Juli": 7,
    "Augusti": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "December": 12,
}


class Source:
    def __init__(self, street, city):
        self.street = street
        self.city = city

    def fetch(self):
        # request to get an adresslist containing the parameter A used for the wasteschedule request.
        adresslist = requests.get(
            API_URLS["address_search"], params={"svar": self.street}
        )
        adresslist.raise_for_status()

        adresstaddict = (self.street.lower(), self.city.lower())
        adresstadjoined = "|".join(adresstaddict)
        adresslistalines = adresslist.text.lower().splitlines()
        for line in adresslistalines:
            if adresstadjoined in line:
                A = line.split("|")[-1]

        payload = {"hsG": self.street, "hsO": self.city, "nrA": A}
        payload_str = urllib.parse.urlencode(payload, encoding="cp1252")
        # request for the wasteschedule
        wasteschedule = requests.get(API_URLS["collection"], params=payload_str)
        wasteschedule.raise_for_status()

        soup = BeautifulSoup(wasteschedule.text, "html.parser")

        entries = []
        # get a list of all tags with waste collection days for the current year
        for wasteday in soup.find_all("td", "styleDayHit"):
            wasteday_wastetype = wasteday.parent.parent
            # find month and year for given day
            monthyear = wasteday_wastetype.find_previous(
                "td", "styleMonthName"
            ).contents
            monthyear_parts = str(monthyear).split("-")
            month = MONTH_MAP[monthyear_parts[0].strip(" []/'")]
            year = int(monthyear_parts[1].strip(" []/'"))
            day = int(
                str(wasteday_wastetype.find("div", "styleInteIdag").contents).strip(
                    " []/'"
                )
            )
            # list of bins collected for given day
            for td in wasteday_wastetype.contents[3].find_all("td"):
                if td.has_attr("class"):
                    waste = str(td.get_attribute_list("class")).strip(" []/'")
                    entries.append(
                        Collection(
                            t=NAME_MAP.get(waste),
                            # t = waste, #used when identifying new types of bins
                            date=datetime.date(year, month, day),
                            icon=ICON_MAP.get(waste),
                        )
                    )
        return entries
