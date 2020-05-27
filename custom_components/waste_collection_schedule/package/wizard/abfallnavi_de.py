#!/usr/bin/python3

import inquirer
import requests
import json


def main():
    # select service
    service_choices = [
        ("Aachen", "aachen"),
        ("AWA Entsorgungs GmbH", "zew2"),
        ("Bergisch Gladbach", "aw-bgl2"),
        ("Bergischer Abfallwirtschaftverbund", "bav"),
        ("Dinslaken", "din"),
        ("Dorsten", "dorsten"),
        ("Gütersloh", "gt2"),
        ("Halver", "hlv"),
        ("Kreis Coesfeld", "coe"),
        ("Kreis Heinsberg", "krhs"),
        ("Kreis Pinneberg", "pi"),
        ("Kreis Warendorf", "krwaf"),
        ("Lindlar", "lindlar"),
        ("Lüdenscheid", "stl"),
        ("Norderstedt", "nds"),
        ("Nürnberg", "nuernberg"),
        ("Roetgen", "roe"),
        ("EGW Westmünsterland", "wml2"),
    ]
    questions = [
        inquirer.List(
            "service",
            choices=service_choices,
            message="Select service provider for district [Landkreis]",
        )
    ]
    answers = inquirer.prompt(questions)

    SERVICE_URL = f"https://{answers['service']}-abfallapp.regioit.de/abfall-app-{answers['service']}"

    # get cities
    r = requests.get(f"{SERVICE_URL}/rest/orte")
    r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
    cities = json.loads(r.text)
    city_choices = []
    for city in cities:
        city_choices.append((city["name"], city["id"]))

    questions = [
        inquirer.List(
            "city_id", choices=city_choices, message="Select municipality [Kommune/Ort]"
        )
    ]
    ort = inquirer.prompt(questions)["city_id"]

    # get streets
    r = requests.get(f"{SERVICE_URL}/rest/orte/{ort}/strassen")
    r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
    streets = json.loads(r.text)
    street_choices = []
    for street in streets:
        street_choices.append((street["name"], street["id"]))

    questions = [
        inquirer.List("strasse", choices=street_choices, message="Select street")
    ]
    answers.update(inquirer.prompt(questions))

    # get list of house numbers
    r = requests.get(f"{SERVICE_URL}/rest/strassen/{answers['strasse']}")
    r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
    house_numbers = json.loads(r.text)
    house_number_choices = []
    for hausNr in house_numbers.get("hausNrList", {}):
        # {"id":5985445,"name":"Adalbert-Stifter-Straße","hausNrList":[{"id":5985446,"nr":"1"},
        house_number_choices.append((hausNr["nr"], hausNr["id"]))

    if len(house_number_choices) > 0:
        questions = [
            inquirer.List(
                "hausnummer",
                choices=house_number_choices,
                message="Select house number",
            )
        ]
        answers.update(inquirer.prompt(questions))

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: abfallnavi_de")
    print("      args:")
    for key, value in answers.items():
        print(f"        {key}: {value}")


if __name__ == "__main__":
    main()
