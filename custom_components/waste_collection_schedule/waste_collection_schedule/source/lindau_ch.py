import json
from datetime import datetime
from bs4 import BeautifulSoup

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Abfall Lindau"
DESCRIPTION = "Source for Lindau waste collection."
URL = "https://www.lindau.ch/abfalldaten"
TEST_CASES = {
    "Tagelswangen": {"city": "Tagelswangen", "types": "kehricht, grungut, papier und karton, altmetalle, hackseldienst"},
    "Grafstal": {"city": "190", "types": "grungut, papier und karton"},
}


class Source:
    def __init__(self, city, types):
        self._city = city
        self._types = types

    def fetch(self):

    
        response = requests.get("https://www.lindau.ch/abfalldaten")
        
        html = BeautifulSoup(response.text, 'html.parser')

        table = html.find('table', attrs={'id':'icmsTable-abfallsammlung'})
        data = json.loads(table.attrs['data-entities'])

        entries = []
        for item in data['data']:

            if self._city in item['abfallkreisIds'] or self._city in item['abfallkreisNameList']:
                next_pickup = item['_anlassDate-sort'].split()[0]
                next_pickup_date = datetime.fromisoformat(next_pickup).date()

                waste_type = BeautifulSoup(item['name'],'html.parser').text
                waste_type_sorted = BeautifulSoup(item['name-sort'],'html.parser').text
                
                if waste_type_sorted == "kehricht" and waste_type_sorted in self._types:
                    icon = "mdi:trash-can"
                    entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))
                elif waste_type_sorted == "grungut" and waste_type_sorted in self._types:
                    icon = "mdi:leaf" 
                    entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))
                elif waste_type_sorted == "hackseldienst" and waste_type_sorted in self._types:
                    icon = "mdi:leaf" 
                    entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))
                elif waste_type_sorted == "papier und karton" and waste_type_sorted in self._types:
                    icon = "mdi:package-variant" 
                    entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))
                elif waste_type_sorted == "altmetalle" and waste_type_sorted in self._types:
                    icon = "mdi:nail" 
                    entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))
                else:
                    icon = "mdi:trash-can"
                    entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))
                
        return entries
