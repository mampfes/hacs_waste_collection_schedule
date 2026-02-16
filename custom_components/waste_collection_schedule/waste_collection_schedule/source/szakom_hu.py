# Source script for Szákom Nonprofit Kft. (Százhalombatta)
# Author: Ferenc Kurucz
# Source: http://szakom.battanet.hu/UserFiles/file/2025/1216/sszakomtit25121613150.pdf

import datetime
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions)

TITLE = "Szákom (Százhalombatta)" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for Szákom Nonprofit Kft. (Százhalombatta)"  # Describe your source
COUNTRY = "hu"
URL = "https://www.szakom.hu"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Test_Lakotelep": {"area_communal": "Lakótelep | hétfő, szerda, péntek", "area_recycle": "Damjanich u.-Benta patak közötti rész, Óváros | csütörtök", "area_green": "Damjanich u.-Benta patak közötti rész | hétfő"},
    "Test_Ovaros": {"area_communal": "Családi házas | kedd", "area_recycle": "Damjanich u.-Benta patak közötti rész, Óváros | csütörtök", "area_green": "Óváros | csütörtök"},
    "Test_Dunafured": {"area_communal": "Családi házas | kedd, péntek", "area_recycle": "Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | csütörtök", "area_green": "Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | szerda"},
}

ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "Kommunális": "mdi:trash-can",
    "Szelektív": "mdi:recycle",
    "Zöldhulladék": "mdi:leaf",
}

NAME_MAP = {
    "Kommunális": "Communal",
    "Szelektív": "Selective",
    "Zöldhulladék": "Green",
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Choose the correct area within Százhalombatta for each waste type.",
}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "area_communal": "Area within Százhalombatta",
        "area_recycle": "Area within Százhalombatta",
        "area_green": "Area within Százhalombatta",
    },
}

PARAM_TRANSLATIONS = { # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "area_communal": "Communal area",
        "area_recycle": "Recycle area",
        "area_green": "Green area",
    },
}

PARAM_COMMUNAL_AREAS_LIST = [
    "Lakótelep | hétfő, szerda, péntek",
    "Családi házas | kedd",
    "Családi házas | kedd, péntek",
    ]

PARAM_RECYCLE_AREAS_LIST = [
    "Damjanich u.-Benta patak közötti rész, Óváros | csütörtök",
    "Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | csütörtök",
    ]

PARAM_GREEN_AREAS_LIST = [
    "Damjanich u.-Benta patak közötti rész | hétfő",
    "Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | szerda",
    "Óváros | csütörtök",
    ]


#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, area_communal:str, area_recycle:str, area_green:str):  # argX correspond to the args dict in the source configuration
        self._area_communal = area_communal
        self._area_recycle = area_recycle
        self._area_green = area_green

    def fetch(self) -> list[Collection]:
        # check for valid area arguments
        if self._area_communal not in PARAM_COMMUNAL_AREAS_LIST:
            raise SourceArgumentNotFoundWithSuggestions("Invalid area_communal argument", PARAM_COMMUNAL_AREAS_LIST)
        if self._area_recycle not in PARAM_RECYCLE_AREAS_LIST:
            raise SourceArgumentNotFoundWithSuggestions("Invalid area_recycle argument", PARAM_RECYCLE_AREAS_LIST)
        if self._area_green not in PARAM_GREEN_AREAS_LIST:
            raise SourceArgumentNotFoundWithSuggestions("Invalid area_green argument", PARAM_GREEN_AREAS_LIST)
        
        entries = []  # List that holds collection schedule

        # Build communal waste collection entries
        entries += self.build_entries_communal_2026()
        # Build recycle waste collection entries
        entries += self.build_entries_recycle_2026()
        # Build green waste collection entries
        entries += self.build_entries_green_2026()
        
        return entries
    
    def build_entries_communal_2026(self) -> list[Collection]:
        entries = []

        if (self._area_communal == "Lakótelep | hétfő, szerda, péntek"):
            first_regular_collection_date = datetime.date(2026, 1, 2)
            collection_days = [0, 2, 4]  # Monday, Wednesday, Friday
        elif (self._area_communal == "Családi házas | kedd"):
            first_regular_collection_date = datetime.date(2026, 1, 6)
            collection_days = [1]  # Tuesday
        elif (self._area_communal == "Családi házas | kedd, péntek"):
            first_regular_collection_date = datetime.date(2026, 1, 6)
            collection_days = [1, 4]  # Tuesday, Friday
        else:
            return entries  # No valid area selected, return empty list

        # generate collection dates for the year 2026
        current_date = first_regular_collection_date
        end_date = datetime.date(2026, 12, 31)
        
        while current_date <= end_date:
            if current_date.weekday() in collection_days:
                entries.append(
                    Collection(
                        date=current_date,
                        t=NAME_MAP.get("Kommunális"),
                        icon=ICON_MAP.get("Kommunális"),
                    )
                )
            current_date += datetime.timedelta(days=1)

        return entries
    
    def build_entries_recycle_2026(self) -> list[Collection]:
        entries = []

        if (self._area_recycle == "Damjanich u.-Benta patak közötti rész, Óváros | csütörtök"):
            first_regular_collection_date = datetime.date(2026, 1, 1)
            days_between_collections = 14  # every two weeks
        elif (self._area_recycle == "Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | csütörtök"):
            first_regular_collection_date = datetime.date(2026, 1, 8)
            days_between_collections = 14  # every two weeks
        else:
            return entries  # No valid area selected, return empty list

        # generate collection dates for the year 2026
        current_date = first_regular_collection_date
        end_date = datetime.date(2026, 12, 31)
        
        while current_date <= end_date:
            entries.append(
                Collection(
                    date=current_date,
                    t=NAME_MAP.get("Szelektív"),
                    icon=ICON_MAP.get("Szelektív"),
                )
            )
            current_date += datetime.timedelta(days=days_between_collections)

        return entries    
    
    def build_entries_green_2026(self) -> list[Collection]:
        entries = []

        # Calendar for green waste collection consists of two parts, the first part is regular collection every week in the season (March to November),
        # the second part is occasional collection days in winter months (January, February, December).
        if (self._area_green == "Damjanich u.-Benta patak közötti rész | hétfő"):
            first_regular_collection_date = datetime.date(2026, 3, 2)
            days_between_collections = 7  # every week
        elif (self._area_green == "Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | szerda"):
            first_regular_collection_date = datetime.date(2026, 3, 4)
            days_between_collections = 7  # every week
        elif (self._area_green == "Óváros | csütörtök"):
            first_regular_collection_date = datetime.date(2026, 3, 5)
            days_between_collections = 7  # every week
        else:
            return entries  # No valid area selected, return empty list

        # generate the regular collection dates for the year 2026
        current_date = first_regular_collection_date
        end_date = datetime.date(2026, 11, 30)
        
        while current_date <= end_date:
            entries.append(
                Collection(
                    date=current_date,
                    t=NAME_MAP.get("Zöldhulladék"),
                    icon=ICON_MAP.get("Zöldhulladék"),
                )
            )
            current_date += datetime.timedelta(days=days_between_collections)

        # add occasional collection dates in winter months
        if (self._area_green == "Damjanich u.-Benta patak közötti rész | hétfő"):
            occasional_dates = [
                datetime.date(2026, 1, 5),
                datetime.date(2026, 1, 12),
                datetime.date(2026, 2, 9),
                datetime.date(2026, 12, 7),
            ]
        elif (self._area_green == "Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | szerda"):
            occasional_dates = [
                datetime.date(2026, 1, 7),
                datetime.date(2026, 1, 14),
                datetime.date(2026, 2, 11),
                datetime.date(2026, 12, 9),
            ]
        elif (self._area_green == "Óváros | csütörtök"):
            occasional_dates = [
                datetime.date(2026, 1, 8),
                datetime.date(2026, 1, 15),
                datetime.date(2026, 2, 12),
                datetime.date(2026, 12, 10),
            ]

        # generate occasional collection entries
        for date in occasional_dates:
            entries.append(
                Collection(
                    date=date,
                    t=NAME_MAP.get("Zöldhulladék"),
                    icon=ICON_MAP.get("Zöldhulladék"),
                )
            )

        return entries        