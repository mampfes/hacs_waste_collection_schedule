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
    "GoodObjectId": {"arg1": "00000"},  # Example object ID, replace with a valid one
}

API_URL = "https://maps.planogis.org/arcgiswad/rest/services/Sustainability/ServicedAddresses/MapServer/0/query?"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "TRASH": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "BULKY": "mdi:size-xl",
}


#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
    "de": "WIE MAN DIE ARGUMENTE ERHÄLT",
    "it": "COME OTTENERE GLI ARGOMENTI",
    "fr": "COMMENT OBTENIR LES ARGUMENTS",
}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "arg1": "A valid object ID from the Plano GIS service. You can find this by searching for your address on the Plano GIS map and clicking on the address to get the object ID.",
    }
}

PARAM_TRANSLATIONS = { # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "arg1": "Object ID"
    },
    "de": {
        "arg1": "Objekt-ID",
    },
    "it": {
        "arg1": "ID oggetto",
    },
    "fr": {
        "arg1": "ID d'objet"
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    
    def __init__(self, arg1:str):  # argX correspond to the args dict in the source configuration
        self._arg1 = arg1
    def next_weekday(self,d:datetime.date, weekday:int):
        days_ahead = weekday - d.weekday()
        if days_ahead < 0: # Target day already happened this week
            days_ahead += 7
        return d + datetime.timedelta(days_ahead)


    def fetch(self) -> list[Collection]:

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details

        logger = logging.getLogger("plano_gov")
        common_args_pre = "f=json&objectIds="+str(self._arg1)
        common_args_post = "&outFields=ADDRESS%2CBLKY_COLOR%2CBLKY_CURR%2CBLKY_NEXT1%2CBLKY_NEXT2%2CBULKY_DAY%2CDAY_2017%2CHouseNo%2CREC_CURR%2CREC_NEXT1%2CREC_NEXT2%2CREC_WEEK_2017%2CSERVICE%2COBJECTID&outSR=102100&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1"
        common_args = common_args_pre+common_args_post
        
        resp = requests.get(API_URL + common_args)
        if resp.status_code != 200:
          raise Exception(f"Something went wrong in ArcGIS land: {resp.text}") # DO NOT JUST return []
        #raise Exception(resp.text)
        #logger.warning(f"Response from API: {resp.status_code} {resp.text}")
        parsed_resp = resp.json()
        address = parsed_resp['features'][0]['attributes']['ADDRESS']
        bulky_color = parsed_resp['features'][0]['attributes']['BLKY_COLOR']
        bulky_current = parsed_resp['features'][0]['attributes']['BLKY_CURR']
        bulky_next1 = parsed_resp['features'][0]['attributes']['BLKY_NEXT1']
        bulky_next2 = parsed_resp['features'][0]['attributes']['BLKY_NEXT2']

        recycle_current = parsed_resp['features'][0]['attributes']['REC_CURR']
        recycle_next1 = parsed_resp['features'][0]['attributes']['REC_NEXT1']
        recycle_next2 = parsed_resp['features'][0]['attributes']['REC_NEXT2']

        trash_day = parsed_resp['features'][0]['attributes']['DAY_2017']

        logger.warning(f"json parsed: {parsed_resp['features']}")
        ##?&objectIds=41379&
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
        us_holidays = holidays.country_holidays("US", years=curr_year)
        next_trash_day = self.next_weekday(today, trash_day_num) # 0 = Monday, 1=Tuesday, 2=Wednesday...
        next_trash_day_2 = self.next_weekday(next_trash_day+datetime.timedelta(days=1), trash_day_num)
        next_trash_day_3 = self.next_weekday(next_trash_day_2+datetime.timedelta(days=1), trash_day_num)
        
        #if its a holiday, the city bumps the trash day to the next day
        if next_trash_day in us_holidays:
            logger.warning(f"Next trash day {next_trash_day} is a holiday, bumping to next day")
            next_trash_day = next_trash_day + datetime.timedelta(days=1)
        if next_trash_day_2 in us_holidays:
            logger.warning(f"Next next trash day {next_trash_day_2} is a holiday, bumping to next day")
            next_trash_day_2 = next_trash_day_2 + datetime.timedelta(days=1)
        if next_trash_day_3 in us_holidays:
            logger.warning(f"Next next trash day {next_trash_day_2} is a holiday, bumping to next day")
            next_trash_day_3 = next_trash_day_3 + datetime.timedelta(days=1)
        ttype = "TRASH"

        entries.append(
            Collection(
                date = next_trash_day,  # Collection date
                t = ttype,  # Collection type
                icon = ICON_MAP.get(ttype),  # Collection icon
            )
        )
        entries.append(
            Collection(
                date = next_trash_day_2,  # Collection date
                t = ttype,  # Collection type
                icon = ICON_MAP.get(ttype),  # Collection icon
            )
        )
        entries.append(
            Collection(
                date = next_trash_day_3,  # Collection date
                t = ttype,  # Collection type
                icon = ICON_MAP.get(ttype),  # Collection icon
            )
        )
         #bulky trash
         #bulky trash comes back as a month / day, so we need to tack on the year and get a date
         #print(datetime.datetime.strptime(foo,"%B %d %Y"))
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
        logger.warning(f"recycle_current_parts: {recycle_current_parts[0]}")
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