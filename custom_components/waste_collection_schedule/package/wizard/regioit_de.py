#!/usr/bin/python3

import inquirer
import requests
import json


def main():
    # select district
    district_choices = [
        ("Aachen", "aachen"),
        ("Bergisch Gladbach", "aw-bgl2"),
        ("Bergischer Abfallwirtschaftverbund (Engelskirchen)", "bav"),
        ("Coesfeld", "coe"),
        ("Dinslaken", "din"),
        ("Dorsten", "dorsten"),
        ("Gütersloh", "gt2"),
        ("Halver", "hlv"),
        ("Heinsberg", "krhs"),
        ("KRWAF", "krwaf"),
        ("Lindlar", "lindlar"),
        ("Lüdenscheid", "stl"),
        ("Norderstedt", "nds"),
        ("Pinneberg", "pi"),
        ("WML", "wml2"),
        ("ZEW", "zew2"),
    ]
    questions = [
        inquirer.List(
            "district",
            choices=district_choices,
            message="Bitte wählen Sie zuerst den gewünschten Ort/Landkreis aus",
        )
    ]
    answers = inquirer.prompt(questions)

    SERVICE_URL = f"https://{answers['district']}-abfallapp.regioit.de/abfall-app-{answers['district']}"

    # get cities
    r = requests.get(f"{SERVICE_URL}/rest/orte")
    cities = json.loads(r.text)

    city_choices = []
    city_id = {}
    for city in cities:
        city_choices.append((city["name"], city["name"]))
        city_id[city["name"]] = city["id"]

    questions = [
        inquirer.List(
            "ort",
            choices=city_choices,
            message="Bitte wählen Sie zuerst den gewünschten Ort aus",
        )
    ]
    answers.update(inquirer.prompt(questions))

    # get streets
    r = requests.get(f"{SERVICE_URL}/rest/orte/{city_id[answers['ort']]}/strassen")

    streets = json.loads(r.text)

    street_choices = []
    house_numbers = {}
    for street in streets:
        # {'id': 5791880, 'name': 'Aachener Straße', 'hausNrList': [{'id': 5791881, 'nr': '11'}, {'id': 5791894, 'nr': '12'}], 'ort': {'id': 5791873, 'name': 'Aachen'}}
        street_choices.append((street["name"], street["id"]))
        if "hausNrList" in street:
            house_number_choices = []
            for nr in street["hausNrList"]:
                house_number_choices.append((nr["nr"], nr["id"]))
            if len(house_number_choices) > 0:
                house_numbers[street["id"]] = house_number_choices

    questions = [
        inquirer.List(
            "strasse",
            choices=street_choices,
            message="Bitte wählen Sie zuerst die gewünschte Strasse aus",
        )
    ]
    answers.update(inquirer.prompt(questions))

    if answers["strasse"] in house_numbers:
        questions = [
            inquirer.List(
                "hnr",
                choices=house_numbers[answers["strasse"]],
                message="Bitte wählen Sie zuerst die gewünschte Hausnummer aus",
            )
        ]
        answers.update(inquirer.prompt(questions))

    # get fraktionen
    r = requests.get(f"{SERVICE_URL}/rest/fraktionen")

    fraktionen = json.loads(r.text)
    answers["fraktion"] = []
    for fraktion in fraktionen:
        answers["fraktion"].append(f"{fraktion['id']}  # {fraktion['name']}")

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: regioit_de")
    print("      args:")
    print(f"        kalender: {answers['district']}")
    print(f"        ort: {answers['ort']}")
    print(f"        strasse: {answers['strasse']}")
    print(f"        hnr: {answers.get('hnr', 'None')}")
    print(f"        fraktion:")
    for f in answers["fraktion"]:
        print(f"          - {f}")


if __name__ == "__main__":
    main()
