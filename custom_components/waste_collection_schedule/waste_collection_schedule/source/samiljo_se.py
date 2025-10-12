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
    "januari": 1,
    "februari": 2,
    "mars": 3,
    "april": 4,
    "maj": 5,
    "juni": 6,
    "juli": 7,
    "augusti": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
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
        A = None
        for line in adresslistalines:
            if streetcityjoined in line:
                A = line.split("|")[3]
                break
        
        if A is None:
            raise Exception("Address not found, please verify the street name and city are correct.")

        payload = {"hsG": self.street, "hsO": self.city, "nrA": A}
        payload_str = urllib.parse.urlencode(payload, encoding="cp1252")
        # request for the wasteschedule
        wasteschedule = requests.get(API_URLS["collection"], params=payload_str)
        wasteschedule.raise_for_status()

        soup = BeautifulSoup(wasteschedule.text, "html.parser")

        entries = []
        # Extended list of bin types to cover all possible collection types
        bin_types = [
            'HKARL1', 'HKARL1-H', 'HKARL2', 'HKARL2-H',
            'FKARL1', 'FKARL1-H', 'FKARL2', 'FKARL2-H', 
            'HMAT', 'HMAT-H', 'HREST', 'HREST-H',
            'HOSORT', 'HOSORT-H', 'FOSORT', 'FOSORT-H',
            'HREST-HK', 'HREST-HK-H', 'HKARL1-HK', 'HKARL1-HK-H',
            'TRG', 'TRG-H', 'FREST-HK', 'FREST-HK-H',
            'FKARL1-HK', 'FKARL1-HK-H', 'FREST', 'FREST-H'
        ]
        
        for bin_type in bin_types:
            elements = soup.find_all("td", class_=bin_type)
            
            for element in elements:
                # Find the day cell containing this bin collection
                day_cell = element
                steps = 0
                while day_cell and steps < 10:  # Prevent infinite loop
                    day_cell = day_cell.parent
                    steps += 1
                    
                    if day_cell and day_cell.name == 'td' and day_cell.get('class'):
                        day_classes = day_cell.get('class')
                        
                        # Check if this is a day cell
                        if any('styleDay' in cls for cls in day_classes):
                            break
                            
                    if day_cell and day_cell.name == 'body':
                        day_cell = None
                        break
                
                if not day_cell:
                    continue
                
                # Find day number
                day_element = day_cell.find("div", ["styleInteIdag", "styleIdag"])
                if day_element:
                    day_text = day_element.get_text().strip()
                    if day_text.isdigit():
                        day = int(day_text)
                        
                        # Find month
                        month_element = day_cell.find_previous("td", "styleMonthName")
                        if month_element:
                            month_text = month_element.get_text().strip()
                            
                            # Parse month and year
                            if '-' in month_text:
                                month_part, year_part = month_text.split('-', 1)
                                month_name = month_part.strip().lower()
                                year = int(year_part.strip())
                                
                                if month_name in MONTH_MAP:
                                    month = MONTH_MAP[month_name]
                                    
                                    # Create collection entry
                                    t = NAME_MAP.get(bin_type, bin_type)
                                    icon = ICON_MAP.get(bin_type)
                                    entries.append(
                                        Collection(
                                            t=t,
                                            icon=icon,
                                            date=datetime.date(year, month, day),
                                        )
                                    )
        
        return entries
