import datetime
from ..collection import Collection
import requests

DESCRIPTION = "Source for ecoharmonogram.pl"
URL = "ecoharmonogram.pl"
TEST_CASES = {
    "TestName": {"town_input": "Krzeszowice", "street_input": "Wyki", "house_number_input": ""}
}
TITLE = "ecoharmonogram.pl"

headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json',
}

towns_url = "https://ecoharmonogram.pl/api/api.php?action=getTowns"
scheduled_periods_url = "https://ecoharmonogram.pl/api/api.php?action=getSchedulePeriods"
streets_url = "https://ecoharmonogram.pl/api/api.php?action=getStreets"
schedules_url = "https://ecoharmonogram.pl/api/api.php?action=getSchedules"


class Source:
    def __init__(self, town, street=None, house_number=None):
        self.town_input = town
        self.street_input = street
        self.house_number_input = house_number

    def fetch(self):
        town_response = requests.get(towns_url, headers=headers)
        town_response.encoding = "utf-8-sig"

        town_date = town_response.json()

        matching_towns = filter(lambda x: self.town_input.lower() in x.get('name').lower(), town_date.get('towns'))
        town = list(matching_towns)[0]

        scheduled_perionds_response = requests.get(scheduled_periods_url + "&townId=" + town.get("id"), headers=headers)
        scheduled_perionds_response.encoding = "utf-8-sig"

        town_date = scheduled_perionds_response.json()
        schedule_periods = town_date.get("schedulePeriods")

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
