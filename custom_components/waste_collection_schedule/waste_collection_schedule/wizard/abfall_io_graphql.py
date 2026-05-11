#!/usr/bin/env python3

import site
from pathlib import Path

import inquirer
import requests

# add module directory to path
package_dir = Path(__file__).resolve().parents[2]
site.addsitedir(str(package_dir))
from waste_collection_schedule.service.AbfallIOGraphQL import SERVICE_MAP  # type: ignore # isort:skip # noqa: E402

INIT_URL = "https://api.abfall.io"
GQL_URL = "https://widgets.abfall.io/graphql"
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
}


def gql(api_key, query, variables=None):
    r = requests.post(
        GQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={
            **HEADERS,
            "Content-Type": "application/json",
            "x-abfallplus-api-key": api_key,
        },
    )
    r.raise_for_status()
    return r.json().get("data", {})


def get_api_key(service_key):
    r = requests.get(INIT_URL, params={"key": service_key}, headers=HEADERS)
    if r.status_code == 401:
        raise ValueError(
            f"Key '{service_key}' was rejected. Make sure you have the correct v3 service key "
            "(find it in your browser's Network tab when loading your provider's collection schedule page)."
        )
    r.raise_for_status()
    config = r.json()
    return config["apiKey"], config["settings"].get("PUB_ABFALLTYPEN", [])


def search_city(api_key, query):
    data = gql(
        api_key,
        """
        query GetCities($query: String) {
            cities(query: $query) {
                id
                name
                idHouseNumber
                districtsCount
                appointmentsSupported
            }
        }
    """,
        {"query": query},
    )
    return data.get("cities", [])


def get_districts(api_key, city_id):
    data = gql(
        api_key,
        """
        query GetDistricts($cityId: ID!) {
            city(id: $cityId) {
                districts {
                    id
                    name
                    idHouseNumber
                }
            }
        }
    """,
        {"cityId": city_id},
    )
    return data.get("city", {}).get("districts", [])


def get_streets(api_key, parent_type, parent_id):
    data = gql(
        api_key,
        f"""
        query GetStreets($id: ID!) {{
            {parent_type}(id: $id) {{
                streets {{
                    id
                    name
                    idHouseNumber
                }}
            }}
        }}
    """,
        {"id": parent_id},
    )
    return data.get(parent_type, {}).get("streets", [])


def get_house_numbers(api_key, street_id, district_id=None):
    data = gql(
        api_key,
        """
        query GetHouseNumbers($streetId: ID!, $idDistrict: ID) {
            street(id: $streetId) {
                houseNumbers(idDistrict: $idDistrict) {
                    id
                    name
                }
            }
        }
    """,
        {"streetId": street_id, "idDistrict": district_id},
    )
    return data.get("street", {}).get("houseNumbers", [])


def get_waste_types(api_key, house_number_id):
    data = gql(
        api_key,
        """
        query HouseNumber($houseNumberId: ID!) {
            houseNumber(id: $houseNumberId) {
                wasteTypes {
                    id
                    name
                }
            }
        }
    """,
        {"houseNumberId": house_number_id},
    )
    return data.get("houseNumber", {}).get("wasteTypes", [])


def main():
    # Select service provider or enter key manually
    provider_choices = [(s["title"], s["service_id"]) for s in SERVICE_MAP]
    provider_choices.append(("Enter key manually", "__manual__"))

    answers = inquirer.prompt(
        [
            inquirer.List(
                "key", choices=provider_choices, message="Select service provider"
            ),
        ]
    )
    service_key = answers["key"]

    if service_key == "__manual__":
        answers = inquirer.prompt(
            [
                inquirer.Text(
                    "key",
                    message="Enter your service key (find it in browser Network tab when loading your provider's schedule page)",
                )
            ]
        )
        service_key = answers["key"].strip()

    print("Connecting to abfall.io...")
    api_key, pub_waste_types = get_api_key(service_key)

    # City search
    while True:
        answers = inquirer.prompt(
            [
                inquirer.Text(
                    "city_query",
                    message="Search for your city (enter part of the name)",
                ),
            ]
        )
        cities = search_city(api_key, answers["city_query"])
        supported = [c for c in cities if c.get("appointmentsSupported")]
        if not supported:
            print(
                "No cities found with appointments support. Try a different search term."
            )
            continue
        break

    city = inquirer.prompt(
        [
            inquirer.List(
                "city",
                choices=[(c["name"], c) for c in supported],
                message="Select your city",
            ),
        ]
    )["city"]

    id_house_number = city.get("idHouseNumber")
    district_id = None

    # Navigate districts if present
    if city["districtsCount"] > 0 and not id_house_number:
        districts = get_districts(api_key, city["id"])
        district = inquirer.prompt(
            [
                inquirer.List(
                    "d",
                    choices=[(d["name"], d) for d in districts],
                    message="Select your district",
                ),
            ]
        )["d"]
        id_house_number = district.get("idHouseNumber")
        district_id = district["id"]

    # Navigate streets if still no idHouseNumber
    if not id_house_number:
        parent_type = "district" if district_id else "city"
        parent_id = district_id if district_id else city["id"]
        streets = get_streets(api_key, parent_type, parent_id)
        if not streets:
            print("No streets found for this location.")
            return

        street = inquirer.prompt(
            [
                inquirer.List(
                    "s",
                    choices=[(s["name"], s) for s in streets],
                    message="Select your street",
                ),
            ]
        )["s"]
        id_house_number = street.get("idHouseNumber")

        # Navigate individual house numbers if needed
        if not id_house_number:
            house_numbers = get_house_numbers(api_key, street["id"], district_id)
            if len(house_numbers) == 1:
                id_house_number = house_numbers[0]["id"]
            elif house_numbers:
                hn = inquirer.prompt(
                    [
                        inquirer.List(
                            "hn",
                            choices=[(h["name"], h) for h in house_numbers],
                            message="Select your house number",
                        ),
                    ]
                )["hn"]
                id_house_number = hn["id"]

    if not id_house_number:
        print("Could not determine idHouseNumber for this location.")
        return

    # Optional: filter waste types
    waste_types = get_waste_types(api_key, id_house_number)
    selected_types = None
    if waste_types:
        answers = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "waste_types",
                    choices=[(wt["name"], wt["id"]) for wt in waste_types],
                    default=[wt["id"] for wt in waste_types],
                    message="Select waste types to include (space to toggle, enter to confirm)",
                )
            ]
        )
        if set(answers["waste_types"]) != {wt["id"] for wt in waste_types}:
            selected_types = answers["waste_types"]

    print("\nCopy the following into your configuration.yaml:\n")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: abfall_io_graphql")
    print("      args:")
    print(f'        key: "{service_key}"')
    print(f"        idHouseNumber: {id_house_number}")
    if selected_types:
        print("        wasteTypes:")
        for wt in selected_types:
            print(f'          - "{wt}"')


if __name__ == "__main__":
    main()
