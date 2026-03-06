import logging
from datetime import date, timedelta

import requests
import re
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    )

TITLE = "Värmdö Sophämntning"
DESCRIPTION = "Source Värmdö household waste collection."
URL = "https://www.varmdo.se"
URL_schedule_list = "https://www.varmdo.se/byggabomiljo/avfallochatervinning/alltomavfallochatervinning/avfallshamtning/hamtveckoravfallfastlandet.4.4fd26e29194d31bcc1fa6ed.html"

# Init logger
_LOGGER = logging.getLogger(__name__)

TEST_CASES = {
    "Rosenmalmsvägen": {"street_address": "Rosenmalmsvägen"},
    "Abborrberget": {"street_address": "Abborrberget"},
    "Idskäret": {"street_address": "Idskäret"},
    #"Fail address": {"street_address": "Not_exist"},
}
COUNTRY = "se"

ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Bio": "mdi:leaf",
}

class Source:
    def __init__(
        self,
        street_address: str,
    ):
        _LOGGER.debug(
                "Initiate Värmdö waste."
            )
        # Remove numbers from street_address
        self._street_address = re.sub(r'\d+', '', street_address)

    def fetch(self):
        data = {}
        response = requests.get(URL_schedule_list,
            data=data,
            timeout=30
        )
        _LOGGER.debug("HTTP get of Värmdö waste url: "+ \
            str(response.status_code))
        
        
        soup = BeautifulSoup(response.text, "html.parser")
        cell = soup.find('td', text=re.compile(self._street_address, re.I))
        
        if not cell:
            raise SourceArgumentException(
                "street_address",
                f"Failed to find address for: {self._street_address}",
            )
            
        row = cell.parent
        weekday = row.findAll("td")[1].text.lower()
        
        if not weekday:
            raise SourceArgumentException(
                "street_address",
                f"Failed to find address for: {self._street_address}",
            )
        
        _LOGGER.debug("Värmdö waste day cell content: "+ \
            str(weekday))
        
        # Weeknumer today
        #print(date.today().isocalendar()[1])
        
        next_pickup_date = date.today()
        
        # Test text in td cell for day in week
        #0 = "Monday", 1 = "Tuesday"
        if "måndag" in weekday:
            next_pickup = 0
        elif "tisdag" in weekday:
            next_pickup = 1
        elif "onsdag" in weekday:
            next_pickup = 2  
        elif "torsdag" in weekday:
            next_pickup = 3
        elif "fredag" in weekday:
            next_pickup = 4
        elif "lördag" in weekday:
            next_pickup = 5
        else:
            next_pickup = 6
        
        # Test weeknumber even / odd for td text
        if "jämna" in weekday:
            next_pickup_week = 0
        else:
            next_pickup_week = 1
            
        #print("pickup day: "+ str(next_pickup) + " week:"+ str(next_pickup_week))

        entries = []
        
        for i in range(0, 4):        
            waste_type = "Trash"
            icon = "mdi:trash-can"
            
            while next_pickup_date.weekday() != next_pickup or (next_pickup_date.isocalendar()[1] % 2 != next_pickup_week):
                next_pickup_date += timedelta(days=1)
                #print("test date: "+ str(next_pickup_date.strftime('%Y-%m-%d')))
                #print("test date - weekday: "+str(next_pickup_date.weekday()) +" week number: "+ str(next_pickup_date.isocalendar()[1]))
                
            next_pickup_date = next_pickup_date
            #print("Found day: "+ str(next_pickup_date.strftime('%Y-%m-%d')))
            entries.append(Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can")
                    ))
            
            # Contiune for next
            next_pickup_date += timedelta(days=1)

        return entries
