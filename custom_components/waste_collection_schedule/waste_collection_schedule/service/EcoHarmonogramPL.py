import sys

import requests

towns_url = "https://ecoharmonogram.pl/api/api.php?action=getTowns"
community_towns_url = "https://ecoharmonogram.pl/api/api.php?action=getTownsForCommunity"
scheduled_periods_url = "https://ecoharmonogram.pl/api/api.php?action=getSchedulePeriods"
streets_url = "https://ecoharmonogram.pl/api/api.php?action=getStreets"
schedules_url = "https://ecoharmonogram.pl/api/api.php?action=getSchedules"

headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json',
}


class Ecoharmonogram:
    @staticmethod
    def fetch_schedules(sp, street):
        payload = {'streetId': street.get("id"), 'schedulePeriodId': sp.get("id")}
        schedules_response = requests.get(
            schedules_url,
            headers=headers, params=payload)
        schedules_response.encoding = "utf-8-sig"
        schedules_response = schedules_response.json()
        return schedules_response

    @staticmethod
    def fetch_streets(sp, town, street, house_number):
        payload = {'streetName': str(street), 'number': str(house_number), 'townId': town.get("id"),
                   'schedulePeriodId': sp.get("id")}

        streets_response = requests.get(
            streets_url, headers=headers, params=payload)
        streets_response.encoding = "utf-8-sig"
        streets = streets_response.json().get("streets")
        return streets

    @staticmethod
    def fetch_scheduled_periods(town):
        payload = {'townId': town.get("id")}
        scheduled_perionds_response = requests.get(scheduled_periods_url, headers=headers, params=payload)
        scheduled_perionds_response.encoding = "utf-8-sig"
        schedule_periods_data = scheduled_perionds_response.json()
        return schedule_periods_data

    @staticmethod
    def fetch_town():
        town_response = requests.get(towns_url, headers=headers)
        town_response.encoding = "utf-8-sig"
        town_data = town_response.json()
        return town_data

    @staticmethod
    def fetch_town_with_community(community):
        payload = {'communityId': community}
        town_response = requests.get(community_towns_url, headers=headers, params=payload)
        town_response.encoding = "utf-8-sig"
        town_data = town_response.json()
        return town_data

    @staticmethod
    def print_possible_sides(town_input, district_input, street_input, house_number_input):
        town_data = Ecoharmonogram.fetch_town()
        matching_towns = filter(lambda x: town_input.lower() in x.get('name').lower(), town_data.get('towns'))
        matching_towns_district = filter(lambda x: district_input.lower() in x.get('district').lower(), matching_towns)

        town = list(matching_towns_district)[0]

        schedule_periods_data = Ecoharmonogram.fetch_scheduled_periods(town)
        schedule_periods = schedule_periods_data.get("schedulePeriods")

        for sp in schedule_periods:
            streets = Ecoharmonogram.fetch_streets(sp, town, street_input, house_number_input)
            for street in streets:
                print(street.get("sides"))


if __name__ == '__main__':
    Ecoharmonogram.print_possible_sides(sys.argv[1], sys.argv[2] or "", sys.argv[3] or "", sys.argv[4] or "")
