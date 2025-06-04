import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Ecoservice atliekos"
DESCRIPTION = 'Source for UAB "Ecoservice".'
URL = "https://ecoservice.lt/grafikai/"
TEST_CASES = {
    "Jono Glaubico g. 10-1 (Vilnius)": {
        "waste_object_ids": "'13-L-115261', 13-P-505460,13-S-500496"
    },
    "Parko g. 1 (Pilies I k.)": {
        "waste_object_ids": "94-L-002776"
    },
    "D. Poškos g. 26 (Vilnius)": {
        "waste_object_ids": ["13-Z-001848"]
    },
    "Empty list 1 - must fail>": {},
    "Empty list 2 - must fail>": {
        "waste_object_ids": ""
    },
    "Bad ids - must fail>": {
        "waste_object_ids": "101358, 100858, 100860"
    }
}

TYPE_MAP = {
    "municipal_small": {
        "icon": "mdi:trash-can",
        "name": "Buitinės atliekos"
    },
    "package_small": {
        "icon": "mdi:recycle",
        "name": "Antrinės žaliavos (popierius/plastikas)"
    },
    "glass_small": {
        "icon": "mdi:glass-fragile",
        "name": "Antrinės žaliavos (stiklas)"
    },
    "green":{
        "icon": "mdi:leaf",
        "name": "Žaliosios atliekos"
    }
}

EXTRA_INFO = [
    {
        "url": "https://ecoservice.lt", 
        "title": "Ecoservice atliekos"
    }
]

PARAM_DESCRIPTIONS = {
    "en": {
        "waste_object_ids": "Waste object ID, or IDs separated by commas."
    },
    "lt": {
        "waste_object_ids": "Konteinerio vienas arba keli ID, atskirti kableliais."
    }
}

PARAM_TRANSLATIONS  = {
    "en": {
        "waste_object_ids": "e.g. '13-L-115261'"
    },
    "lt": {
        "waste_object_ids": "pvz. '13-L-115261'"
    }
}


class Source:
    API_URL = "https://ecoapp.ecoservice.lt/"

    def __init__(
        self, waste_object_ids=None
    ):
        if waste_object_ids is None:
            waste_object_ids = []
        self._waste_object_ids = waste_object_ids

    def fetch(self):

        if not self._waste_object_ids:
            raise ValueError("Waste object IDs must be provided.")

        # split user string from GUI into a list (however, list comes from YAML)
        if not isinstance(self._waste_object_ids, list):            
            self._waste_object_ids = self._waste_object_ids.split(",")
        
        entries = []
        
        for obj_id in self._waste_object_ids:
            if not isinstance(obj_id, str):
                raise ValueError(
                    "Waste object IDs must be strings, got: {}".format(type(obj_id))
                )

            try:
                # cleanup user string
                obj_id = obj_id.strip()
                obj_id = obj_id.replace('"', '')
                obj_id = obj_id.replace("'", "")        
                
                # fetch container data
                c_query = {
                    "r": "api/calendar",
                    "key": "fd1d20bcd36e86504ac4bad2d88a2caa",  # magic API key, not clear when and if it changes
                    "containerId": obj_id,
                    "getSpecificStuff": "container_id"
                }       
        
                r = requests.get(
                    self.API_URL,
                    params=c_query,
                )
                r.raise_for_status()
                
                container = json.loads(r.text)

                self.check_for_container_error(container)

                # fetch container collection schedule
                s_query = {
                    "r": "api/calendar",
                    "key": "fd1d20bcd36e86504ac4bad2d88a2caa",  # magic API key, not clear when and if it changes
                    "containerId": container[0]["key"],
                    "getSpecificStuff": "container_map"
                }

                r = requests.get(
                    self.API_URL,
                    params=s_query,
                )
                r.raise_for_status()
                
                schedule = json.loads(r.text)

                if len(schedule) == 0:
                    raise Exception(
                        "Error: failed to fetch collection schedule data"
                    )
                
                for date, value in schedule.items():
                    if value:
                        entries.append(
                            Collection(
                                date=datetime.strptime(date, "%Y-%m-%d").date(),
                                t=TYPE_MAP.get(container[0]["Type"], {}).get("name"),
                                icon=TYPE_MAP.get(container[0]["Type"], {}).get("icon"),
                            )
                        )
                    
                if len(entries) == 0:
                    raise Exception(
                        "Error: no collection schedule data found for container ID: {}".format(obj_id)
                    )  
            
            except Exception as e:
                raise Exception (
                    f"Error fetching data for waste object ID {obj_id}: {e}"                
                )

        return entries


    def check_for_container_error(self, container):
        if not container or len(container) == 0 or "key" not in container[0]:
            raise Exception(
                "Error: failed to fetch container data"
                )
            
