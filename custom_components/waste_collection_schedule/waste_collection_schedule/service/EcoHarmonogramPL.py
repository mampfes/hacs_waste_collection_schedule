import sys

import requests

API_URL = "https://ecoharmonogram.pl/api/api.php"

SUPPORTED_APPS = [
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
    "bialapodlaska" "slupsk",
    "trzebownisko",
    "zory",
]


class Ecoharmonogram:
    def __init__(self, app: str | None = None):
        self._headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        }
        self._app = app if app else None

    def do_request(
        self, action: str, payload: dict[str, str], url: str = API_URL
    ) -> requests.Response:
        params = payload.copy()
        params["action"] = action
        if self._app:
            params["customApp"] = self._app
        response = requests.get(url, headers=self._headers, params=params)
        response.encoding = "utf-8-sig"
        return response

    def fetch_schedules(self, sp, streetId):
        payload = {"streetId": streetId, "schedulePeriodId": sp.get("id")}
        schedules_response = self.do_request("getSchedules", payload)
        schedules_response.encoding = "utf-8-sig"
        schedules_response = schedules_response.json()
        return schedules_response

    def fetch_streets(self, sp, town, street, house_number):
        payload = {
            "streetName": str(street),
            "number": str(house_number),
            "townId": town.get("id"),
            "schedulePeriodId": sp.get("id"),
        }

        streets_response = self.do_request("getStreets", payload)
        streets_response.encoding = "utf-8-sig"
        streets = streets_response.json().get("streets")
        return streets

    def fetch_scheduled_periods(self, town):
        payload = {"townId": town.get("id")}
        scheduled_perionds_response = self.do_request("getSchedulePeriods", payload)
        scheduled_perionds_response.encoding = "utf-8-sig"
        schedule_periods_data = scheduled_perionds_response.json()
        return schedule_periods_data

    def fetch_town(self):
        town_response = self.do_request("getTowns", {})
        town_response.encoding = "utf-8-sig"
        town_data = town_response.json()
        return town_data

    def fetch_town_with_community(self, community):
        payload = {"communityId": community}
        town_response = self.do_request(action="getTownsForCommunity", payload=payload)
        town_response.encoding = "utf-8-sig"
        town_data = town_response.json()
        return town_data

    def print_possible_sides(
        self, town_input, district_input, street_input, house_number_input
    ):
        town_data = self.fetch_town()
        matching_towns = filter(
            lambda x: town_input.lower() in x.get("name").lower(),
            town_data.get("towns"),
        )
        matching_towns_district = filter(
            lambda x: district_input.lower() in x.get("district").lower(),
            matching_towns,
        )

        town = list(matching_towns_district)[0]

        schedule_periods_data = self.fetch_scheduled_periods(town)
        schedule_periods = schedule_periods_data.get("schedulePeriods")

        for sp in schedule_periods:
            streets = self.fetch_streets(sp, town, street_input, house_number_input)
            for street in streets:
                for streetId in street.get("id").split(","):
                    schedules_response = self.fetch_schedules(sp, streetId)
                    print(schedules_response.get("street").get("sides"))


def print_markdown_table() -> None:
    table_data: dict[str | None, list[str]] = {}

    for app in [None] + SUPPORTED_APPS:
        ecoharmonogram = Ecoharmonogram(app)
        towns = ecoharmonogram.fetch_town()["towns"]
        town_names = [t["name"] for t in towns]
        table_data[app] = town_names

    duplicates_count: dict[str, int] = {}

    for app, towns in table_data.items():
        if app is None:
            continue

        for town in towns:
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
        print(f"duplicate Towns wiht No App: {duplicates_with_total}")

    print("|APP | TOWN|")
    print("|-|-|")
    for app, towns in table_data.items():
        app = app or "NO APP (LEAVE EMPTY)"
        print(f"|{app}|{', '.join(towns)}|")


if __name__ == "__main__":
    Ecoharmonogram(sys.argv[5] if len(sys.argv) > 5 else None).print_possible_sides(
        sys.argv[1], sys.argv[2] or "", sys.argv[3] or "", sys.argv[4] or ""
    )
