#!/usr/bin/python3

import inquirer
import requests
import json


def main():
    # select service
    service_choices = [
        ("Altötting", "aoe"),
        ("Aurich", "lka"),
        ("Bad Homburg vdH", "hom"),
        ("Barnim", "bdg"),
        # ('Groß-Gerau', 'aws'),
        # ('Hattersheim am Main', 'ham'),
        # ('Ingolstadt', 'inkb'),
        ("Lübbecke", "lue"),
        ("Minden", "sbm"),
        ("Recklinghausen", "ksr"),
        ("Rhein-Hunsrück", "rhe"),
        ("Uckermark", "udg"),
        ("ZAW", "zaw"),
    ]
    questions = [
        inquirer.List(
            "service_id",
            choices=service_choices,
            message="Bitte wählen Sie zuerst den gewünschten Landkreis aus",
        )
    ]
    answers = inquirer.prompt(questions)

    # select city
    args = {"r": "cities"}
    r = requests.get(
        f"https://{answers['service_id']}.jumomind.com/mmapp/api.php", params=args
    )
    cities = json.loads(r.text)

    city_choices = []
    for city in cities:
        # {'name': 'Altötting', '_name': 'Altötting', 'id': '24', 'region_code': '02', 'area_id': '24', 'img': None, 'has_streets': True}
        city_choices.append((city["name"], city["id"]))

    questions = [
        inquirer.List(
            "city_id",
            choices=city_choices,
            message="Bitte wählen Sie den gewünschten Ort aus",
        )
    ]
    answers.update(inquirer.prompt(questions))

    # select area
    args = {"r": "streets", "city_id": answers["city_id"]}
    r = requests.get(
        f"https://{answers['service_id']}.jumomind.com/mmapp/api.php", params=args
    )
    areas = json.loads(r.text)

    area_choices = []
    house_numbers = {}
    for area in areas:
        # {'name': 'Adalbert-Stifter-Str.', '_name': 'Adalbert-Stifter-Str.', 'id': '302', 'area_id': '48'}
        # {"name":"ACHATWEG","_name":"ACHATWEG","id":"355008","area_id":"085080001","houseNumberFrom":"0001","houseNumberTo":"0001","comment":"","houseNumbers":[["0001","085080001"],["0003","085080003"],["0004","085080004"],["0005","085080005"],["0006","085080006"]]},
        area_choices.append((area["name"], area["area_id"]))
        house_number_choices = []
        if "houseNumbers" in area:
            for hnr in area["houseNumbers"]:
                house_number_choices.append((hnr[0], hnr[1]))
            house_numbers[area["area_id"]] = house_number_choices

    questions = [
        inquirer.List(
            "area_id",
            choices=area_choices,
            message="Bitte wählen Sie die gewünschte Strasse aus",
        )
    ]
    answers.update(inquirer.prompt(questions))

    if answers["area_id"] in house_numbers:
        questions = [
            inquirer.List(
                "area_id",
                choices=house_numbers[answers["area_id"]],
                message="Bitte wählen Sie die gewünschte Hausnummer aus",
            )
        ]
        answers.update(inquirer.prompt(questions))

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: jumomind_de")
    print("      args:")
    print(f"        service_id: {answers['service_id']}")
    print(f"        city_id: {answers['city_id']}")
    print(f"        area_id: {answers['area_id']}")


if __name__ == "__main__":
    main()
