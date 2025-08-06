import requests
import logging
import datetime
from datetime import date, timedelta
from waste_collection_schedule import Collection

TITLE = "City of Plano" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for plano.gov"  # Describe your source
COUNTRY = "us"  # ISO 3166-1 alpha-2 country code, e.g. "DE" for Germany, "US" for United States
URL = "https://www.plano.gov/630/Residential-Collection-Schedules"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "GoodObjectId3Days": {"objectId": "00000","daysToGenerate":"3"},  # Example object ID, replace with a valid one
    "GoodObjectId5Days": {"objectId": "00000","daysToGenerate":"5"},  # Example object ID, replace with a valid one
}

API_URL = "https://maps.planogis.org/arcgiswad/rest/services/Sustainability/ServicedAddresses/MapServer/0/query?"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "TRASH": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "BULKY": "mdi:size-xl",
}
WEEKDAYMAP = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
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
        "objectId": "Object ID",
        "daysToGenerate": "Number of days to generate for default collection (default: 3)"
    },
    "de": {
        "objectId": "Objekt-ID",
        "daysToGenerate": "Anzahl der Tage, die für die Standardkollektion generiert werden sollen (Standard: 3)"
    },
    "it": {
        "objectId": "ID oggetto",
        "daysToGenerate": "Numero di giorni da generare per la collezione predefinita (predefinito: 3)"
    },
    "fr": {
        "objectId": "ID d'objet",
        "daysToGenerate": "Nombre de jours à générer pour la collection par défaut (par défaut : 3)"
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    
    def __init__(self, objectId:str, daysToGenerate:int):  # argX correspond to the args dict in the source configuration
        self.object_id = objectId
        self.trash_days_to_generate = daysToGenerate if daysToGenerate is not None else 3  # Default to 3 days if not provided
    
    def is_us_federal_holiday(self,check_date: date) -> bool:
        year = check_date.year

        # Fixed-date holidays
        fixed_holidays = {
            date(year, 1, 1),    # New Year's Day
            date(year, 6, 19),   # Juneteenth National Independence Day
            date(year, 7, 4),    # Independence Day
            date(year, 11, 11),  # Veterans Day
            date(year, 12, 25),  # Christmas Day
        }

        # Helper to find nth weekday in a month
        def nth_weekday(month, weekday, n):
            first_day = date(year, month, 1)
            days_to_add = (weekday - first_day.weekday() + 7) % 7 + (n - 1) * 7
            return first_day + timedelta(days=days_to_add)

        # Helper to find last weekday in a month
        def last_weekday(month, weekday):
            last_day = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
            days_back = (last_day.weekday() - weekday + 7) % 7
            return last_day - timedelta(days=days_back)

        # Variable-date holidays
        variable_holidays = {
            nth_weekday(1, 0, 3),   # Martin Luther King Jr. Day: 3rd Monday in January
            nth_weekday(2, 0, 3),   # Presidents' Day: 3rd Monday in February
            last_weekday(5, 0),     # Memorial Day: last Monday in May
            nth_weekday(9, 0, 1),   # Labor Day: 1st Monday in September
            nth_weekday(10, 0, 2),  # Columbus Day: 2nd Monday in October
            nth_weekday(11, 3, 4),  # Thanksgiving Day: 4th Thursday in November
        }

        return check_date in fixed_holidays or check_date in variable_holidays


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

        resp = requests.get(API_URL,params=params)
        
        if resp.status_code != 200:
          raise Exception(f"Something went wrong in ArcGIS land: {resp.text}") # DO NOT JUST return []
        
        parsed_resp = resp.json()
        if('features' not in parsed_resp or len(parsed_resp['features']) == 0):
            raise Exception(f"No data found for object ID {self.object_id}. Please check your object ID.")
        
        bulky_dates_str = \
            [
            parsed_resp['features'][0]['attributes']['BLKY_CURR'], 
            parsed_resp['features'][0]['attributes']['BLKY_NEXT1'],
            parsed_resp['features'][0]['attributes']['BLKY_NEXT2']
            ]

        recycle_dates_str = \
            [
                parsed_resp['features'][0]['attributes']['REC_CURR'],
                parsed_resp['features'][0]['attributes']['REC_NEXT1'],
                parsed_resp['features'][0]['attributes']['REC_NEXT2']
            ]

        trash_day = parsed_resp['features'][0]['attributes']['DAY_2017']


        today = datetime.date.today()
        curr_year = today.year
        
         
        entries = []  # List that holds collection schedule
       
        #standard trash

        #For standard trash we only get the day of the week, so we need to convert it to a date
       
        trash_day_num = WEEKDAYMAP.get(trash_day, None)
        
        if(trash_day_num is None):
            raise Exception(f"Invalid trash day: {trash_day}")
        
        next_trash_days = []
        

        for i in range(int(self.trash_days_to_generate)):
            # Calculate the next trash day based on the current date and the trash day number
            next_trash_day = self.next_weekday(today + datetime.timedelta(weeks=i), trash_day_num)
            
            # If the next trash day is a holiday, bump it to the next day
            if self.is_us_federal_holiday(next_trash_day):
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
         
        bulky_dates_str = [bulky + " " + str(curr_year) for bulky in bulky_dates_str]  # e.g. "January 1 2023"
        bulky_dates = [datetime.datetime.strptime(bulky, "%B %d %Y").date() for bulky in bulky_dates_str]
       

        ttype = "BULKY"
        for bulky_date in bulky_dates:
            entries.append(
                Collection(
                    date = bulky_date,  # Collection date
                    t = ttype,  # Collection type
                    icon = ICON_MAP.get(ttype),  # Collection icon
                )
            )
      
       #recycling
        ttype = "RECYCLE"
        #recyling is returned with a similar curr, next1, next2 format like bulky
        #however, it actually returns 2-3 dates in the curr depending on how many recycling occurences there will be
        #because recycling is every other week.
        recycle_dates = []
        
        
        for recycle in recycle_dates_str:
            recycle_parts = recycle.split(",")
            recycle_month = recycle_parts[0].strip().split(" ")[0]
            recycle_date = datetime.datetime.strptime(recycle_parts[0] + " " + str(curr_year), "%B %d %Y").date()
            recycle_dates.append(recycle_date)
            if len(recycle_parts) > 1:
                recycle_dates.append(datetime.datetime.strptime(str(recycle_date.month) + " " + recycle_parts[1] + " " + str(curr_year), "%m %d %Y").date())
            if len(recycle_parts) > 2:
                recycle_dates.append(datetime.datetime.strptime(str(recycle_date.month) + " " + recycle_parts[2] + " " + str(curr_year), "%m %d %Y").date())
        
        

        for recycle_date in recycle_dates:
            entries.append(
                Collection(
                    date = recycle_date,  # Collection date
                    t = ttype,  # Collection type
                    icon = ICON_MAP.get(ttype),  # Collection icon
                )
            )
        return entries