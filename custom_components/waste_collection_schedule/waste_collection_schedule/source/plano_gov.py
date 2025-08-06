import requests
import logging
import datetime
import holidays
from waste_collection_schedule import Collection

TITLE = "City of Plano" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for plano.gov"  # Describe your source
COUNTRY = "us"  # ISO 3166-1 alpha-2 country code, e.g. "DE" for Germany, "US" for United States
URL = "https://www.plano.gov/630/Residential-Collection-Schedules"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "GoodObjectId": {"arg1": "00000","arg2":"3"},  # Example object ID, replace with a valid one
    "GoodObjectId": {"arg1": "00000","arg2":"5"},  # Example object ID, replace with a valid one
}

API_URL = "https://maps.planogis.org/arcgiswad/rest/services/Sustainability/ServicedAddresses/MapServer/0/query?"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "TRASH": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "BULKY": "mdi:size-xl",
}


#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Use [The Plano interactive waste map](https://www.plano.gov/630/Residential-Collection-Schedules) to search for and retrieve your object ID using browser dev tools or a capture tool like Fiddler"

}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "arg1": "A valid object ID from the Plano GIS service. You can find this by searching for your address on the Plano GIS map and clicking on the address to get the object ID.",
    }
}

PARAM_TRANSLATIONS = { # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "arg1": "Object ID",
        "arg2": "Number of days to generate for default collection (default: 3)"
    },
    "de": {
        "arg1": "Objekt-ID",
        "arg2": "Anzahl der Tage, die für die Standardkollektion generiert werden sollen (Standard: 3)"
    },
    "it": {
        "arg1": "ID oggetto",
        "arg2": "Numero di giorni da generare per la collezione predefinita (predefinito: 3)"
    },
    "fr": {
        "arg1": "ID d'objet",
        "arg2": "Nombre de jours à générer pour la collection par défaut (par défaut : 3)"
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    
    def __init__(self, arg1:str, arg2:int):  # argX correspond to the args dict in the source configuration
        self.object_id = arg1
        self.trash_days_to_generate = arg2 if arg2 is not None else 3  # Default to 3 days if not provided
    
    def next_weekday(self,d:datetime.date, weekday:int):
        days_ahead = weekday - d.weekday()
        if days_ahead < 0: # Target day already happened this week
            days_ahead += 7
        return d + datetime.timedelta(days_ahead)


    def fetch(self) -> list[Collection]:

        logger = logging.getLogger("plano_gov")
        params: dict[str, str | int | bool] = {
            "f": "json",
            "objectIds": self.object_id,
            "outFields": "ADDRESS,BLKY_COLOR,BLKY_CURR,BLKY_NEXT1,BLKY_NEXT2,BULKY_DAY,DAY_2017,HouseNo,REC_CURR,REC_NEXT1,REC_NEXT2,REC_WEEK_2017,SERVICE,OBJECTID",
            "outSR": 102100,
            "returnGeometry": False,
            "spatialRel": "esriSpatialRelIntersects",
            "where": "1=1",
        }

        # common_args_pre = "f=json&objectIds="+str(self.object_id)
        # common_args_post = "&outFields=ADDRESS%2CBLKY_COLOR%2CBLKY_CURR%2CBLKY_NEXT1%2CBLKY_NEXT2%2CBULKY_DAY%2CDAY_2017%2CHouseNo%2CREC_CURR%2CREC_NEXT1%2CREC_NEXT2%2CREC_WEEK_2017%2CSERVICE%2COBJECTID&outSR=102100&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1"
        # common_args = common_args_pre+common_args_post
        
        resp = requests.get(API_URL,params=params)
        
        if resp.status_code != 200:
          raise Exception(f"Something went wrong in ArcGIS land: {resp.text}") # DO NOT JUST return []
        
        parsed_resp = resp.json()
        if('features' not in parsed_resp or len(parsed_resp['features']) == 0):
            raise Exception(f"No data found for object ID {self.object_id}. Please check your object ID.")
        
        bulky_current = parsed_resp['features'][0]['attributes']['BLKY_CURR']
        bulky_next1 = parsed_resp['features'][0]['attributes']['BLKY_NEXT1']
        bulky_next2 = parsed_resp['features'][0]['attributes']['BLKY_NEXT2']

        recycle_current = parsed_resp['features'][0]['attributes']['REC_CURR']
        recycle_next1 = parsed_resp['features'][0]['attributes']['REC_NEXT1']
        recycle_next2 = parsed_resp['features'][0]['attributes']['REC_NEXT2']

        trash_day = parsed_resp['features'][0]['attributes']['DAY_2017']


        today = datetime.date.today()
        curr_year = today.year
        
         
        entries = []  # List that holds collection schedule
       
        #standard trash

        #For standard trash we only get the day of the week, so we need to convert it to a date
         
        weekdaymap = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }
        trash_day_num = weekdaymap.get(trash_day, None)
        
        if(trash_day_num is None):
            raise Exception(f"Invalid trash day: {trash_day}")
        
        next_trash_days = []
        us_holidays = holidays.country_holidays("US", years=curr_year)

        for i in range(int(self.trash_days_to_generate)):
            # Calculate the next trash day based on the current date and the trash day number
            next_trash_day = self.next_weekday(today + datetime.timedelta(weeks=i), trash_day_num)
            
            # If the next trash day is a holiday, bump it to the next day
            if next_trash_day in us_holidays:
                logger.warning(f"Next trash day {next_trash_day} is a holiday, bumping to next day")
                next_trash_day += datetime.timedelta(days=1)
            
            next_trash_days.append(next_trash_day)

        ttype = "TRASH"

      
        for next_trash_day in next_trash_days:
            entries.append(
                Collection(
                    date = next_trash_day,  # Collection date
                    t = ttype,  # Collection type
                    icon = ICON_MAP.get(ttype),  # Collection icon
                )
            )
         #bulky trash
         #bulky trash comes back as a month / day, so we need to tack on the year and get a date
         
        bulky_current = bulky_current + " " + str(curr_year)  # e.g. "January 1 2023"
        bulky_next1 = bulky_next1 + " " + str(curr_year)  # e.g. "January 1 2023"
        bulky_next2 = bulky_next2 + " " + str(curr_year)  # e.g. "January 1 2023"
        bulky_current_date = datetime.datetime.strptime(bulky_current, "%B %d %Y").date()
        bulky_next1_date = datetime.datetime.strptime(bulky_next1, "%B %d %Y").date()
        bulky_next2_date = datetime.datetime.strptime(bulky_next2, "%B %d %Y").date()

        ttype = "BULKY"
        entries.append(
            Collection(
                date = bulky_current_date,  # Collection date
                t = ttype,  # Collection type
                icon = ICON_MAP.get(ttype),  # Collection icon
            )
        )
        entries.append(
            Collection(
                date = bulky_next1_date,  # Collection date
                t = ttype,  # Collection type
                icon = ICON_MAP.get(ttype),  # Collection icon
            )
        )
        entries.append(
            Collection(
                date = bulky_next2_date,  # Collection date
                t = ttype,  # Collection type
                icon = ICON_MAP.get(ttype),  # Collection icon
            )
        )
        #recycling
        ttype = "RECYCLE"
        #recyling is returned with a similar curr, next1, next2 format like bulky
        #however, it actually returns 2-3 dates in the curr depending on how many recycling occurences there will be
        #because recycling is every other week.
        recycle_current_parts = recycle_current.split(",")  # e.g. "January 1 2023, January 15 2023"
        recycle_current_dates = []
        recycle_current_dates.append(datetime.datetime.strptime(recycle_current_parts[0] + " " + str(curr_year), "%B %d %Y").date())
        if len(recycle_current_parts) > 1:
            recycle_current_dates.append(datetime.datetime.strptime(str(recycle_current_dates[0].month) + " " + recycle_current_parts[1] + " " + str(curr_year), "%m %d %Y").date())
        if len(recycle_current_parts) > 2:
            recycle_current_dates.append(datetime.datetime.strptime(str(recycle_current_dates[0].month) + " " + recycle_current_parts[2] + " " + str(curr_year), "%m %d %Y").date())

        recycle_next1_dates = []
        recycle_next1_parts = recycle_next1.split(",")
        
        recycle_next1_dates.append(datetime.datetime.strptime(recycle_next1_parts[0] + " " + str(curr_year), "%B %d %Y").date())
        if len(recycle_next1_parts) > 1:
            recycle_next1_dates.append(datetime.datetime.strptime(str(recycle_next1_dates[0].month) + " " + recycle_next1_parts[1] + " " + str(curr_year), "%m %d %Y").date())
        if len(recycle_next1_parts) > 2:
            recycle_next1_dates.append(datetime.datetime.strptime(str(recycle_next1_dates[0].month) + " " + recycle_next1_parts[2] + " " + str(curr_year), "%m %d %Y").date())
        
        recycle_next2_dates = []
        recycle_next2_parts = recycle_next2.split(",")
        recycle_next2_dates.append(datetime.datetime.strptime(recycle_next2_parts[0] + " " + str(curr_year), "%B %d %Y").date())
        if len(recycle_next2_parts) > 1:
            recycle_next2_dates.append(datetime.datetime.strptime(str(recycle_next2_dates[0].month) + " " + recycle_next2_parts[1] + " " + str(curr_year), "%m %d %Y").date())
        if len(recycle_next2_parts) > 2:
            recycle_next2_dates.append(datetime.datetime.strptime(str(recycle_next2_dates[0].month) + " " + recycle_next2_parts[2] + " " + str(curr_year), "%m %d %Y").date())
        
        recycle_dates = recycle_current_dates + recycle_next1_dates + recycle_next2_dates

        for recycle_date in recycle_dates:
            entries.append(
                Collection(
                    date = recycle_date,  # Collection date
                    t = ttype,  # Collection type
                    icon = ICON_MAP.get(ttype),  # Collection icon
                )
            )
       
       


        return entries