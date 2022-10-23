import datetime
from ..collection import Collection
import requests

# Notes:
# Ecoharmonogram is a platform providing its customers with ability of managing and publishing
# waste collection schedules for multiple communities in Poland.
# It provides services in two flavours: in the ecoharmonogram native app and in the town/community branded app.
# Locations supported by the branded apps are still available via the public API, but are not exposed only
# when querying for the given CommunityId.
# If communityId is provided, source will use it, otherwise search for natively supported towns.

DESCRIPTION = "Source for ecoharmonogram.pl"
URL = "ecoharmonogram.pl"
TEST_CASES = {
    "Branded community": {"community": "108", "town": "Gdańsk", "street": "Jabłoniowa", "house_number": "55"},
    "Native App": {"town": "Krzeszowice", "street": "Wyki", "house_number": ""},
}
TITLE = "ecoharmonogram.pl"

headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json',
}

towns_url = "https://ecoharmonogram.pl/api/api.php?action=getTowns"
towns_for_community_url = "https://ecoharmonogram.pl/api/api.php?action=getTownsForCommunity"
scheduled_periods_url = "https://ecoharmonogram.pl/api/api.php?action=getSchedulePeriods"
streets_url = "https://ecoharmonogram.pl/api/api.php?action=getStreets"
schedules_url = "https://ecoharmonogram.pl/api/api.php?action=getSchedules"


class Source:
    def __init__(self, town, community="", street="", house_number=""):
        self.town_input = town
        self.street_input = street
        self.house_number_input = house_number
        self.community_input = community

    def fetch(self):
        if self.community_input == "":
        # Retrieve towns that are exposed in the native ecoharmonogram app
            town_response = requests.get(towns_url, headers=headers)
        else:
            town_response = requests.get(towns_for_community_url + "&communityId=" + self.community_input, headers=headers)    
        
        town_response.encoding = "utf-8-sig"

        town_data = town_response.json()
        
        matching_towns = filter(lambda x: self.town_input.lower() in x.get('name').lower(), town_data.get('towns'))
        town = list(matching_towns)[0]

        scheduled_perionds_response = requests.get(scheduled_periods_url + "&townId=" + town.get("id"), headers=headers)
        scheduled_perionds_response.encoding = "utf-8-sig"

        town_data = scheduled_perionds_response.json()
        schedule_periods = town_data.get("schedulePeriods")

        for sp in schedule_periods:
            streets_response = requests.get(
                streets_url + "&streetName=" + str(self.street_input) + "&number=" + str(
                    self.house_number_input) + "&townId=" + town.get("id") +
                "&schedulePeriodId=" + sp.get("id"), headers=headers)
            streets_response.encoding = "utf-8-sig"
            streets = streets_response.json().get("streets")
            for s in streets:
                schedules_response = requests.get(
                    schedules_url + "&streetId=" + s.get("id") + "&schedulePeriodId=" + sp.get("id"),
                    headers=headers)
                schedules_response.encoding = "utf-8-sig"
                schedules_response = schedules_response.json()

        schedules_raw = schedules_response.get('schedules')
        schedules_descriptions_dict = dict()
        schedules_descriptions_raw = schedules_response.get('scheduleDescription')

        for sd in schedules_descriptions_raw:
            schedules_descriptions_dict[sd.get('id')] = sd

        schedules = []
        for s in schedules_raw:
            z = s.copy()
            get = schedules_descriptions_dict.get(s.get('scheduleDescriptionId'))
            z['name'] = get.get("name")
            schedules.append(z)

        entries = []
        for sch in schedules:
            days = sch.get("days").split(';')
            month = sch.get("month")
            year = sch.get("year")
            for d in days:
                entries.append(
                    Collection(
                        datetime.date(int(year), int(month), int(d)),
                        sch.get('name')
                    )
                )

        return entries
