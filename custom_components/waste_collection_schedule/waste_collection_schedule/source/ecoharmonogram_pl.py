import datetime
from typing import cast

from ..collection import Collection
from ..exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
    SourceArgumentRequiredWithSuggestions,
)
from ..service.EcoHarmonogramPL import (
    SUPPORTED_APPS_LITERAL,
    Ecoharmonogram,
    Schedule,
    ScheduleDescription,
    SchedulePeriod,
    Street,
    StreetResponse,
    Town,
)

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Fill in Town, Street, Housenumber and District and press confirm. If any other field is required, it will tell you with a dropdown menu of suggestions. If your Town is not found, you might need to provide the App argument. (take a look in the linked documentation below, there is a list of towns with their corresponding App argument)",
    # "pl": "Wypełnij pola Miasto, Ulica, Numer domu i Dzielnica i naciśnij potwierdź. Jeśli wymagane jest inne pole, zostanie to powiedziane z rozwijanym menu sugestii. Jeśli Twoje miasto nie zostanie znalezione, być może będziesz musiał podać argument App. (zobacz w poniższej dokumentacji, jest lista miast z odpowiadającymi im argumentami App)",
}

GROUP_DESCRIPTION_EN = "Select Collection group to limit results to a specific group within a waste type (e.g. 'Papier (1 x miesiąc)' for Paper collected once a month). Leave empty and only fill if it fails, you'll then see a list of available groups."
GROUP_DESCRIPTION_PL = "Wybierz grupę zbiórki, aby ograniczyć wyniki do konkretnej grupy w obrębie typu odpadów (np. 'Papier (1 x miesiąc)' dla papieru zbieranego raz w miesiącu). Pozostaw puste i wypełnij tylko wtedy, gdy wystąpi błąd, wtedy zobaczysz listę dostępnych grup."

PARAM_TRANSLATIONS = {
    "en": {
        "town": "Town",
        "street": "Street",
        "house_number": "House number",
        "district": "District",
        "additional_sides_matcher": "Additional Sides Matcher",
        "community": "Community",
        "g1": "Group 1",
        "g2": "Group 2",
        "g3": "Group 3",
        "g4": "Group 4",
        "g5": "Group 5",
    },
    # "pl": {
    #     "town": "Miasto",
    #     "street": "Ulica",
    #     "house_number": "Numer domu",
    #     "district": "Dzielnica",
    #     "additional_sides_matcher": "Matcher dodatkowych stron zbiórki",
    #     "community": "Społeczność",
    #     "g1": "Grupa 1",
    #     "g2": "Grupa 2",
    #     "g3": "Grupa 3",
    #     "g4": "Grupa 4",
    #     "g5": "Grupa 5",
    # },
}
PARAM_DESCRIPTIONS = {
    "en": {
        "town": "Town",
        "street": "Street",
        "house_number": "House number",
        "district": "District",
        "additional_sides_matcher": "Additional matcher for collection sides",
        "community": "Community",
        "g1": GROUP_DESCRIPTION_EN,
        "g2": GROUP_DESCRIPTION_EN,
        "g3": GROUP_DESCRIPTION_EN,
        "g4": GROUP_DESCRIPTION_EN,
        "g5": GROUP_DESCRIPTION_EN,
    },
    # "pl": {
    #     "town": "Miasto",
    #     "street": "Ulica",
    #     "house_number": "Numer domu",
    #     "district": "Dzielnica",
    #     "additional_sides_matcher": "Dodatkowy matcher dla stron zbiórki",
    #     "community": "Społeczność",
    #     "g1": GROUP_DESCRIPTION_PL,
    #     "g2": GROUP_DESCRIPTION_PL,
    #     "g3": GROUP_DESCRIPTION_PL,
    #     "g4": GROUP_DESCRIPTION_PL,
    #     "g5": GROUP_DESCRIPTION_PL,
    # },
}


# {"schedulePeriods":[{"id":"7059","startDate":"2025-01-01","endDate":"2025-03-31","changeDate":"2024-12-19 23:05:18"},{"id":"7946","startDate":"2025-04-01","endDate":"2025-10-31","changeDate":"2025-05-07 09:42:53"}]}

TITLE = "Ecoharmonogram"
DESCRIPTION = "Source for ecoharmonogram.pl"
URL = "https://ecoharmonogram.pl"
TEST_CASES = {
    "Częstochowa Częstochowa Bartnicza 9": {
        "town": "Częstochowa",
        "street": "Bartnicza",
        "house_number": "9",
        "district": "Częstochowa",
        "additional_sides_matcher": "Szkło (1 x miesiąc)",
        "g1": "Firmy (5 fakcji + popiół 2,3,4 x mc)",
        "g2": "Zmieszane (5 x miesiąc)",
        "g3": "Bio (3 x miesiąc)",
        "g4": "Metale i Tworzywa (4 x miesiąc)",
        "g5": "Papier (1 x miesiąc)",
    },
    "Simple test case": {
        "town": "Krzeszowice",
        "street": "Wyki",
        "house_number": "1",
        "additional_sides_matcher": "Zabudowa jednorodzinna",
    },
    "Sides multi test case": {
        "town": "Częstochowa",
        "house_number": "1",
        "street": "Boczna",
        "g1": "Firmy (5 frakcji)",
        "g2": "Zmieszane (5 x miesiąc)",
        "g3": "Bio (3 x miesiąc)",
        "g4": "Metale i Tworzywa (2 x miesiąc)",
        "g5": "Papier (4 x miesiąc)",
        "additional_sides_matcher": "Szkło (4 x miesiąc)",
    },
    "Sides test case": {
        "town": "Częstochowa",
        "street": "Azaliowa",
        "house_number": "1",
        "g1": "Zabudowa jednorodzinna",
        "additional_sides_matcher": "jedn",
    },
    "Sides multi test case with district": {
        "town": "Borkowo",
        "district": "Pruszcz Gdański",
        "street": "Sadowa",
        "house_number": "1",
        "additional_sides_matcher": "Wielorodzinna - powyżej 7 lokali",
    },
    "Simple test with community": {
        "town": "Gdańsk",
        "street": "Jabłoniowa",
        "house_number": "55",
        "g1": "Zabudowa jednorodzinna",
        "additional_sides_matcher": "",
        # "app": "gdansk",
        "community": "108",
    },
    "Zawiercie, Równa, Zawiercie": {
        "town": "Zawiercie",
        "street": "Równa",
        "house_number": "1",
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
        "g1": "tylko odpady zmieszane",
        "house_number": "1",
    },
    "With app": {
        "town": "Buczków",
        "street": "Buczków",
        "house_number": "1",
        "app": "eco-przyszlosc",
        "additional_sides_matcher": "Zabudowa wielolokalowa i niezamieszkała o zwiększonej częstotliwości",
    },
}


class ScheduleWithName(Schedule):
    name: str


class Source:
    def __init__(
        self,
        town,
        app: SUPPORTED_APPS_LITERAL = None,
        district="",
        street="",
        house_number="",
        additional_sides_matcher="",
        community="",
        g1="",
        g2="",
        g3="",
        g4="",
        g5="",
    ):
        self.town_input = town
        self.street_input = street
        self.house_number_input = house_number
        self.district_input = district
        self.additional_sides_matcher_input = additional_sides_matcher
        self.community_input = community
        self._g1 = g1
        self._g2 = g2
        self._g3 = g3
        self._g4 = g4
        self._g5 = g5

        # house_number should be required as group matching requires it and the App enfoces it too, Keepint it as optional for now to show a better error message
        if not house_number:
            raise SourceArgumentRequired(
                "house_number",
                "House number is required for Ecoharmonogram source.",
            )

        self._groups = {
            "g1": self._g1,
            "g2": self._g2,
            "g3": self._g3,
            "g4": self._g4,
            "g5": self._g5,
        }

        if app:
            self._ecoharmonogram_pl = Ecoharmonogram(app)
        else:
            self._ecoharmonogram_pl = Ecoharmonogram()

    def fetch(self):
        if self.community_input == "":
            town_data = self._ecoharmonogram_pl.fetch_town(self.town_input)
        else:
            town_data = self._ecoharmonogram_pl.fetch_town_with_community(
                self.community_input
            )

        matching_towns = list(
            filter(
                lambda x: self.town_input.lower() in x.get("name").lower(),
                town_data.get("towns"),
            )
        )
        matching_towns_district = list(
            filter(
                lambda x: self.district_input.lower() in x.get("district").lower(),
                matching_towns,
            )
        )

        if len(matching_towns) == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "town",
                self.town_input,
                {x.get("name") for x in town_data.get("towns", [])},
            )
        if len(matching_towns_district) == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "district",
                self.district_input,
                {x.get("district") for x in matching_towns},
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

        schedule_periods_data = self._ecoharmonogram_pl.fetch_scheduled_periods(town)
        schedule_periods = schedule_periods_data.get("schedulePeriods")

        entries = []
        for sp in schedule_periods:
            entries.extend(self._create_entries(sp, town))
        return entries

    def _entry_exists(self, dmy, name, entries: list[Collection]):
        for e in entries:
            if dmy == e.date and name == e.type:
                return True
        return False

    def _get_streets_with_group(self, sp: SchedulePeriod, town: Town) -> StreetResponse:
        groupId = "1"
        choosedStreetIds = ""
        counter = 0
        streets: StreetResponse = {
            "streets": [],
            "groups": {"items": [], "groupId": ""},
        }
        while groupId != "":  # Prevent infinite loop (should probably never happen)
            counter += 1
            if counter > 6:
                raise Exception("Infinite loop detected while fetching groups")
            streets = self._ecoharmonogram_pl.fetch_streets(
                sp,
                town,
                self.street_input,
                self.house_number_input,
                groupId,
                choosedStreetIds,
            )

            groupId = streets["groups"]["groupId"]
            if len(streets["groups"]["items"]) != 0 and groupId in self._groups:
                for g_name, val in self._groups.items():
                    if groupId != g_name:
                        continue
                    if val == "":
                        raise SourceArgumentRequiredWithSuggestions(
                            g_name,
                            val,
                            {x["name"] for x in streets["groups"]["items"]},
                        )
                    group_match = None
                    for group in streets["groups"]["items"]:
                        if group["name"].lower().casefold() == val.lower().casefold():
                            group_match = group
                            choosedStreetIds = group["choosedStreetIds"]
                    if group_match is None:
                        raise SourceArgumentNotFoundWithSuggestions(
                            g_name,
                            val,
                            {x["name"] for x in streets["groups"]["items"]},
                        )

        if len(streets["streets"]) == 1:
            return streets

        if len(streets["streets"]) == 0:
            raise SourceArgumentNotFound(
                "street",
                self.street_input,
            )

        to_return: list[Street] = []
        for street in streets["streets"]:
            if street["sides"] == "":
                to_return.append(street)
            elif self.additional_sides_matcher_input == "":
                raise SourceArgumentRequiredWithSuggestions(
                    "additional_sides_matcher",
                    self.additional_sides_matcher_input,
                    {x["sides"] for x in streets["streets"]},
                )
            elif (
                street["sides"].lower().casefold()
                == self.additional_sides_matcher_input.lower().casefold()
            ):
                to_return.append(street)

        if len(to_return) == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "additional_sides_matcher",
                self.additional_sides_matcher_input,
                {x["sides"] for x in streets["streets"]},
            )

        return streets

    def _create_entries(self, sp: SchedulePeriod, town: Town) -> list[Collection]:
        streets = self._get_streets_with_group(sp, town)

        entries: list[Collection] = []
        for street in streets["streets"]:
            for streetId in street["id"].split(","):
                schedules_response = self._ecoharmonogram_pl.fetch_schedules(
                    sp, streetId
                )
                schedules_raw = schedules_response["schedules"]
                if (
                    self.additional_sides_matcher_input.lower()
                    in schedules_response["street"]["sides"].lower()
                ):
                    schedules_descriptions_dict = dict[str, ScheduleDescription]()
                    schedules_descriptions_raw = schedules_response[
                        "scheduleDescription"
                    ]

                    for sd in schedules_descriptions_raw:
                        schedules_descriptions_dict[sd["id"]] = sd

                    schedules: list[ScheduleWithName] = []
                    for sr in schedules_raw:
                        z: ScheduleWithName = cast(ScheduleWithName, sr.copy())
                        z["name"] = schedules_descriptions_dict[
                            sr["scheduleDescriptionId"]
                        ]["name"]
                        schedules.append(z)

                    for sch in schedules:
                        days = sch["days"].split(";")
                        month = sch["month"]
                        year = sch["year"]
                        for d in days:
                            dmy = datetime.date(int(year), int(month), int(d))
                            name = sch["name"]
                            if not self._entry_exists(dmy, name, entries):
                                entries.append(Collection(dmy, name))
                if self.additional_sides_matcher_input == "":
                    return entries
        return entries
