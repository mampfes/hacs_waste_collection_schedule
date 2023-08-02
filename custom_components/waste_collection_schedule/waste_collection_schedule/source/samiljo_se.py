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
    "HMAT": "mdi:food-apple",
    "HMAT-H": "mdi:food-apple",
    "HREST": "mdi:trash-can",
    "HREST-H": "mdi:trash-can",
    "HOSORT": "mdi:trash-can",
    "HOSORT-H": "mdi:trash-can",
    'FKARL1': "mdi:trash-can",  # Matavfall, Restavfall, Tidningar & Färgat glas
    'FKARL2': "mdi:recycle", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    'FKARL1-H': "mdi:trash-can", # Matavfall, Restavfall, Tidningar & Färgat glas
    'FKARL2-H': "mdi:recycle", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    'FOSORT': "mdi:trash-can",
    'FOSORT-H': "mdi:trash-can",
    'HREST-HK': "mdi:trash-can",
    'HREST-HK-H': "mdi:trash-can",
    'HKARL1-HK': "mdi:trash-can",  # Restavfall, Tidningar & Färgat glas
    'HKARL1-HK-H': "mdi:trash-can",  # Restavfall, Tidningar & Färgat glas
    'TRG': "mdi:leaf",
    'TRG-H': "mdi:leaf",
    'FREST-HK': "mdi:trash-can",
    'FREST-HK-H': "mdi:trash-can",
    'FKARL1-HK-H': "mdi:trash-can",
    'FKARL1-HK': "mdi:trash-can",
    'FREST': "mdi:trash-can",
    'FREST-H': "mdi:trash-can",
}

NAME_MAP = {
    "HKARL1": "Fyrfackskärl 1",  # Matavfall, Restavfall, Tidningar & Färgat glas
    "HKARL1-H": "Fyrfackskärl 1 - Helgvecka", # Matavfall, Restavfall, Tidningar & Färgat glas
    "HKARL2": "Fyrfackskärl 2", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "HKARL2-H": "Fyrfackskärl 2 - Helgvecka", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "HMAT": "Matavfall",
    "HMAT-H": "Matavfall - Helgvecka",
    "HREST": "Restavfall",
    "HREST-H": "Restavfall - Helgvecka",
    "HOSORT": "Blandat Mat- och Restavfall",
    "HOSORT-H": "Blandat Mat- och Restavfall - Helgvecka",
    'FKARL1': "Fyrfackskärl 1",  # Matavfall, Restavfall, Tidningar & Färgat glas
    'FKARL2': "Fyrfackskärl 2", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    'FKARL1-H': "Fyrfackskärl 1 - Helgvecka", # Matavfall, Restavfall, Tidningar & Färgat glas
    'FKARL2-H': "Fyrfackskärl 2 - Helgvecka", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    'FOSORT': "Blandat Mat- och Restavfall",
    'FOSORT-H': "Blandat Mat- och Restavfall - Helgvecka",
    'HREST-HK': "Restavfall med Hemkompost",
    'HREST-HK-H': "Restavfall med Hemkompost - Helgvecka",
    'HKARL1-HK': "Fyrfackskärl 1 med Hemkompost",  # Restavfall, Tidningar & Färgat glas
    'HKARL1-HK-H': "Fyrfackskärl 1 med Hemkompost - Helgvecka",  # Restavfall, Tidningar & Färgat glas
    'TRG': "Trädgårdskärl",
    'TRG-H': "Trädgårdskärl - Helgvecka",
    'FREST-HK': "Restavfall med Hemkompost",
    'FREST-HK-H': "Restavfall med Hemkompost - Helgvecka",
    'FKARL1-HK-H': "Fyrfackskärl 1 med Hemkompost",
    'FKARL1-HK': "Fyrfackskärl 1 med Hemkompost - Helgvecka",
    'FREST': "Restavfall",
    'FREST-H': "Restavfall - Helgvecka",
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

        streetcitylist = (self.street.lower(), self.city.lower())
        streetcityjoined = "|".join(streetcitylist)
        adresslistalines = adresslist.text.lower().splitlines()
        for line in adresslistalines:
            if streetcityjoined in line:
                A = line.split("|")[3]

        payload = {"hsG": self.street, "hsO": self.city, "nrA": A}
        payload_str = urllib.parse.urlencode(payload, encoding="cp1252")
        # request for the wasteschedule
        wasteschedule = requests.get(API_URLS["collection"], params=payload_str)
        wasteschedule.raise_for_status()

        soup = BeautifulSoup(wasteschedule.text, "html.parser")

        #Calender uses diffrent tags for the last week of the month
        wastedays = soup.find_all("td", {"style":"styleDayHit"}) + soup.find_all("td", "styleDayHit")

        entries = []
        # get a list of all tags with waste collection days for the current year
        for wasteday in wastedays:
            wasteday_wastetype = wasteday.parent.parent
            # find month and year for given day
            monthyear = wasteday_wastetype.find_previous(
                "td", "styleMonthName"
            ).contents
            monthyear_parts = str(monthyear).split("-")
            month = MONTH_MAP[monthyear_parts[0].strip(" []/'")]
            year = int(monthyear_parts[1].strip(" []/'"))

            #Diffrent tag on collection day
            day = int(
                str(wasteday_wastetype.find("div", ["styleInteIdag", "styleIdag"]).contents[0])
            )
            # list of bins collected for given day
            for td in wasteday_wastetype.contents[3].find_all("td"):
                if td.has_attr("class"):
                    waste = str(td.get_attribute_list("class")).strip(" []/'")
                    if waste in NAME_MAP:
                        t=NAME_MAP.get(waste)
                        icon=ICON_MAP.get(waste)
                        entries.append(
                            Collection(
                                t=t,
                                icon=icon,
                                date=datetime.date(year, month, day),                       
                            )
                    )
        return entries
