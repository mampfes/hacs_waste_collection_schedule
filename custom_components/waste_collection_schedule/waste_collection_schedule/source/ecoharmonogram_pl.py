import datetime
from ..collection import Collection

from ..service.EcoHarmonogramPL import Ecoharmonogram

DESCRIPTION = "Source for ecoharmonogram.pl"
URL = "ecoharmonogram.pl"
TEST_CASES = {
    "Simple test case": {"town": "Krzeszowice", "street": "Wyki", "house_number": ""},
    "Sides multi test case": {"town": "Częstochowa", "street": "Boczna", "additional_sides_matcher": "wie"},
    "Sides test case": {"town": "Częstochowa", "street": "Azaliowa", "house_number": "1",
                        "additional_sides_matcher": "jedn"}
}
TITLE = "ecoharmonogram.pl"


class Source:
    def __init__(self, town, street="", house_number="", additional_sides_matcher=""):
        self.town_input = town
        self.street_input = street
        self.house_number_input = house_number
        self.additional_sides_matcher_input = additional_sides_matcher

    def fetch(self):

        town_data = Ecoharmonogram.fetch_town()
        matching_towns = filter(lambda x: self.town_input.lower() in x.get('name').lower(), town_data.get('towns'))
        town = list(matching_towns)[0]

        schedule_periods_data = Ecoharmonogram.fetch_scheduled_periods(town)
        schedule_periods = schedule_periods_data.get("schedulePeriods")

        entries = []
        for sp in schedule_periods:
            streets = Ecoharmonogram.fetch_streets(sp, town, self.street_input, self.house_number_input)
            for street in streets:
                if self.additional_sides_matcher_input.lower() in street.get("sides").lower():
                    schedules_response = Ecoharmonogram.fetch_schedules(sp, street)
                    schedules_raw = schedules_response.get('schedules')
                    schedules_descriptions_dict = dict()
                    schedules_descriptions_raw = schedules_response.get('scheduleDescription')

                    for sd in schedules_descriptions_raw:
                        schedules_descriptions_dict[sd.get('id')] = sd

                    schedules = []
                    for sr in schedules_raw:
                        z = sr.copy()
                        get = schedules_descriptions_dict.get(sr.get('scheduleDescriptionId'))
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
                    if self.additional_sides_matcher_input != "":
                        return entries

        return entries
