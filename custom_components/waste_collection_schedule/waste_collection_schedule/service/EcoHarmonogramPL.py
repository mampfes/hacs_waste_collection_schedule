from random import randrange
from typing import Literal, Mapping, TypedDict, get_args

import requests

API_URL = "https://ecoharmonogram.pl/api/api.php"

SUPPORTED_APPS_LITERAL = Literal[
    None,
    "eco-przyszlosc",
    "ogrodzieniec",
    "gdansk",
    "hajnowka",
    "niemce",
    "zgk-info",
    "ilza",
    "swietochlowice",
    "popielow",
    "mierzecice",
    "bialapodlaska",
    "slupsk",
    "trzebownisko",
    "zory",
]

SUPPORTED_APPS = get_args(SUPPORTED_APPS_LITERAL)


class Town(TypedDict):
    id: str
    communityId: str
    name: str
    district: str
    province: str
    icon: str
    isStrNmrReq: str
    schedulePeriodId: int


class Towns(TypedDict):
    towns: list[Town]


class SchedulePeriod(TypedDict):
    id: str
    startDate: str
    endDate: str
    changeDate: str


class SchedulePeriods(TypedDict):
    schedulePeriods: list[SchedulePeriod]


class Street(TypedDict):
    id: str
    name: str
    region: str
    numbers: str
    numberFrom: str
    numberTo: str
    sides: str
    g1: str
    g2: str
    g3: str
    g4: str
    g5: str
    townName: str
    townDistrict: str
    townProvince: str


class StreetGroup(TypedDict):
    streetName: str
    name: str
    choosedStreetIds: str


class StreetGroups(TypedDict):
    items: list[StreetGroup]
    groupId: str


class StreetResponse(TypedDict):
    streets: list[Street]
    groups: StreetGroups


class Schedule(TypedDict):
    id: str
    month: str
    days: str
    year: str
    scheduleDescriptionId: str


class ScheduleDescription(TypedDict):
    id: str
    month: str
    days: str
    year: str
    scheduleDescriptionId: str
    name: str
    description: str
    typeId: str
    color: str
    notificationType: str
    notificationText: str
    notificationDaysBefore: str
    visInCompl: str
    customTextWhenNoDates: str
    doNotShowDates: str


class Search(TypedDict):
    number: str


class ScheduleResponse(TypedDict):
    schedules: list[Schedule]
    scheduleDescription: list[ScheduleDescription]
    street: Street
    town: Town
    schedulePeriod: SchedulePeriod
    name: str
    id: str
    groupname: str
    search: Search
    footer: str


class Ecoharmonogram:
    def __init__(self, app: str | None = None):
        self._headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            # "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }
        self._app = app if app else None
        self._client_id = hex(randrange(0x1000000000000000, 0xFFFFFFFFFFFFFFFF))[2:]

    def do_request(
        self, action: str, payload: Mapping[str, str | int], url: str = API_URL
    ) -> requests.Response:
        params = dict(payload)
        params["action"] = action
        if self._app:
            params["customApp"] = self._app
        params["funcVersion"] = 3
        params["appVersion"] = 107
        params["systemId"] = 1
        params["clientId"] = self._client_id
        params["lng"] = "pl"

        response = requests.post(url, headers=self._headers, data=params)
        response.encoding = "utf-8-sig"
        return response

    def fetch_schedules(self, sp: SchedulePeriod, streetId: str) -> ScheduleResponse:
        payload = {"streetId": streetId, "schedulePeriodId": sp["id"]}
        schedules_response = self.do_request("getSchedules", payload)
        schedules_response.encoding = "utf-8-sig"
        schedules_response_data = schedules_response.json()
        return schedules_response_data

    def fetch_streets(
        self,
        sp: SchedulePeriod,
        town: Town,
        street: str,
        house_number: str | int,
        groupId: int | str = 1,
        choosedStreetIds: str = "",
    ) -> StreetResponse:
        payload: dict[str, str | int] = {
            "streetName": str(street),
            "number": str(house_number),
            "townId": town["id"],
            "schedulePeriodId": sp["id"],
            "groupId": groupId,
            "choosedStreetIds": choosedStreetIds,
        }

        streets_response = self.do_request("getStreets", payload)
        streets_response.encoding = "utf-8-sig"
        streets = streets_response.json()
        return streets

    def fetch_scheduled_periods(self, town: Town) -> SchedulePeriods:
        payload = {"townId": town["id"]}
        scheduled_perionds_response = self.do_request("getSchedulePeriods", payload)
        scheduled_perionds_response.encoding = "utf-8-sig"
        schedule_periods_data = scheduled_perionds_response.json()
        return schedule_periods_data

    def fetch_town(self, town_input: str) -> Towns:
        town_response = self.do_request("getTowns", {"townName": town_input})
        town_response.encoding = "utf-8-sig"
        town_data = town_response.json()
        return town_data

    def fetch_town_with_community(self, community: str) -> Towns:
        payload = {"communityId": community}
        town_response = self.do_request(action="getTownsForCommunity", payload=payload)
        town_response.encoding = "utf-8-sig"
        town_data = town_response.json()
        return town_data

    def print_possible_sides(
        self,
        town_input: str,
        district_input: str,
        street_input: str,
        house_number_input: str | int,
    ) -> None:
        town_data = self.fetch_town(town_input)
        matching_towns = filter(
            lambda x: town_input.lower() in x["name"].lower(),
            town_data["towns"],
        )
        matching_towns_district = filter(
            lambda x: district_input.lower() in x["district"].lower(),
            matching_towns,
        )

        town = list(matching_towns_district)[0]

        schedule_periods_data = self.fetch_scheduled_periods(town)
        schedule_periods = schedule_periods_data["schedulePeriods"]

        for sp in schedule_periods:
            streets = self.fetch_streets(sp, town, street_input, house_number_input)
            for street in streets["streets"]:
                for streetId in street["id"].split(","):
                    schedules_response = self.fetch_schedules(sp, streetId)
                    print(schedules_response["street"]["sides"])


def print_markdown_table() -> None:
    table_data: dict[str | None, list[str]] = {}

    for app in SUPPORTED_APPS:
        ecoharmonogram = Ecoharmonogram(app)
        towns = ecoharmonogram.fetch_town("")["towns"]
        town_names = [t["name"] for t in towns]
        table_data[app] = town_names

    duplicates_count: dict[str, int] = {}

    for app, town_names in table_data.items():
        if app is None:
            continue

        for town in town_names:
            if town in table_data[None]:
                if app not in duplicates_count:
                    duplicates_count[app] = 0
                duplicates_count[app] += 1

    duplicates_with_total = {
        k: {"duplicates": v, "total": len(table_data[k])}
        for k, v in duplicates_count.items()
        if v > 0
    }
    if len(duplicates_with_total) > 0:
        print(f"duplicate Towns with No App: {duplicates_with_total}")

    print("|APP | TOWN|")
    print("|-|-|")
    for app, town_names in table_data.items():
        app = app or "NO APP (LEAVE EMPTY)"
        print(f"|{app}|{', '.join(town_names)}|")


if __name__ == "__main__":
    print_markdown_table()
    # Ecoharmonogram(sys.argv[5] if len(sys.argv) > 5 else None).print_possible_sides(
    #     sys.argv[1], sys.argv[2] or "", sys.argv[3] or "", sys.argv[4] or ""
    # )
