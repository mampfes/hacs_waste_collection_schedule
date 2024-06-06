import datetime

from ..collection import Collection
from ..service.EcoHarmonogramPL import Ecoharmonogram

TITLE = "Ecoharmonogram"
DESCRIPTION = "Source for ecoharmonogram.pl"
URL = "https://ecoharmonogram.pl"
TEST_CASES = {
    "Simple test case": {"town": "Krzeszowice", "street": "Wyki", "house_number": ""},
    "Sides multi test case": {
        "town": "Częstochowa",
        "street": "Boczna",
        "additional_sides_matcher": "wie",
    },
    "Sides test case": {
        "town": "Częstochowa",
        "street": "Azaliowa",
        "house_number": "1",
        "additional_sides_matcher": "jedn",
    },
    "Sides multi test case with district": {
        "town": "Borkowo",
        "district": "Pruszcz Gdański",
        "street": "Sadowa",
        "additional_sides_matcher": "Wielorodzinna - powyżej 7 lokali",
    },
    "Simple test with community": {
        "town": "Gdańsk",
        "street": "Jabłoniowa",
        "house_number": "55",
        "additional_sides_matcher": "",
        "community": "108",
    },
    "Zawiercie, Równa, Zawiercie": {
        "town": "Zawiercie",
        "street": "Równa",
        "district": "Zawiercie",
    },
    "Case for multi id separated with comma": {
        "town": "Zabrze",
        "street": "Leśna",
        "district": "Zabrze",
        "house_number": "1",
    },
    "Case for multiple schedules for the same house": {
        "town": "Nadolice Wielkie",
        "street": "Zbożowa",
        "district": "Czernica",
        "house_number": "1",
    },
}


class Source:
    def __init__(
        self,
        town,
        district="",
        street="",
        house_number="",
        additional_sides_matcher="",
        community="",
    ):
        self.town_input = town
        self.street_input = street
        self.house_number_input = house_number
        self.district_input = district
        self.additional_sides_matcher_input = additional_sides_matcher
        self.community_input = community

    def fetch(self):
        if self.community_input == "":
            town_data = Ecoharmonogram.fetch_town()
        else:
            town_data = Ecoharmonogram.fetch_town_with_community(self.community_input)

        matching_towns = filter(
            lambda x: self.town_input.lower() in x.get("name").lower(),
            town_data.get("towns"),
        )
        matching_towns_district = list(
            filter(
                lambda x: self.district_input.lower() in x.get("district").lower(),
                matching_towns,
            )
        )

        if len(matching_towns_district) == 0:
            raise Exception(
                f"Town {self.town_input} with district {self.district_input} not found"
            )

        town = matching_towns_district[0]

        if len(matching_towns_district) > 1:
            match = False
            for town_district in matching_towns_district:
                if (
                    self.town_input.lower() == town_district.get("name").lower()
                    and self.district_input.lower()
                    == town_district.get("district").lower()
                ):
                    match = True
                    town = town_district
                    break
            if not match:
                matches = list(
                    map(
                        lambda x: "town: "
                        + x.get("name")
                        + ", district:"
                        + x.get("district"),
                        matching_towns_district,
                    )
                )

                raise Exception(
                    f"Found multiple matches but no exact match found {matches}"
                )

        schedule_periods_data = Ecoharmonogram.fetch_scheduled_periods(town)
        schedule_periods = schedule_periods_data.get("schedulePeriods")

        entries = []
        for sp in schedule_periods:
            entries.extend(self._create_entries(sp, town))
        return entries

    def _create_entries(self, sp, town):
        streets = Ecoharmonogram.fetch_streets(
            sp, town, self.street_input, self.house_number_input
        )
        entries = []
        for street in streets:
            for streetId in street.get("id").split(","):
                schedules_response = Ecoharmonogram.fetch_schedules(sp, streetId)
                schedules_raw = schedules_response.get("schedules")
                if (
                    self.additional_sides_matcher_input.lower()
                    in schedules_response.get("street").get("sides").lower()
                ):
                    schedules_descriptions_dict = dict()
                    schedules_descriptions_raw = schedules_response.get(
                        "scheduleDescription"
                    )

                    for sd in schedules_descriptions_raw:
                        schedules_descriptions_dict[sd.get("id")] = sd

                    schedules = []
                    for sr in schedules_raw:
                        z = sr.copy()
                        get = schedules_descriptions_dict.get(
                            sr.get("scheduleDescriptionId")
                        )
                        z["name"] = get.get("name")
                        schedules.append(z)

                    entries = []
                    for sch in schedules:
                        days = sch.get("days").split(";")
                        month = sch.get("month")
                        year = sch.get("year")
                        for d in days:
                            entries.append(
                                Collection(
                                    datetime.date(int(year), int(month), int(d)),
                                    sch.get("name"),
                                )
                            )
                if self.additional_sides_matcher_input != "":
                    return entries
        return entries
