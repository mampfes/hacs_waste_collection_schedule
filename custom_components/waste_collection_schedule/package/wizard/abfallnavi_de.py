#!/usr/bin/python3

import json
import os
import sys

import inquirer
import requests

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from service.AbfallnaviDe import SERVICE_DOMAINS, AbfallnaviDe  # isort:skip


def convert_dict_to_array(d):
    a = []
    for item in d.items():
        a.append((item[1], item[0]))
    return a


def main():
    args = {}

    # select service domain
    questions = [
        inquirer.List(
            "service_id",
            choices=convert_dict_to_array(SERVICE_DOMAINS),
            message="Select service provider for district [Landkreis]",
        )
    ]
    service_id = inquirer.prompt(questions)["service_id"]
    args["service"] = service_id

    # create service
    api = AbfallnaviDe(service_id)

    SERVICE_URL = f"https://{service_id}-abfallapp.regioit.de/abfall-app-{service_id}"

    # select city
    cities = api.get_cities()
    questions = [
        inquirer.List(
            "city_id",
            choices=convert_dict_to_array(cities),
            message="Select municipality [Kommune/Ort]"
        )
    ]
    city_id = inquirer.prompt(questions)["city_id"]
    args["ort"] = cities[city_id]

    # select street
    streets = api.get_streets(city_id)
    questions = [
        inquirer.List(
            "street_id",
            choices=convert_dict_to_array(streets),
            message="Select street"
        )
    ]
    street_id = inquirer.prompt(questions)["street_id"]
    args["strasse"] = streets[street_id]

    # get list of house numbers
    house_numbers = api.get_house_numbers(street_id)
    if len(house_numbers) > 0:
        questions = [
            inquirer.List(
                "house_number_id",
                choices=convert_dict_to_array(house_numbers),
                message="Select house number",
            )
        ]
        house_number_id = inquirer.prompt(questions)["house_number_id"]
        args["hausnummer"] = house_numbers[house_number_id]

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: abfallnavi_de")
    print("      args:")
    for key, value in args.items():
        print(f"        {key}: {value}")


if __name__ == "__main__":
    main()
