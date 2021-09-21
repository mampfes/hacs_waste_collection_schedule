#!/usr/bin/env python3

import inquirer
import requests
import sys
import json

def get_cities():
    r = requests.get("https://www.awsh.de/api_v2/collection_dates/1/orte")
    return json.loads(r.text)

def get_strassen(ort):
    r = requests.get(f"https://www.awsh.de/api_v2/collection_dates/1/ort/{ort}/strassen")
    return json.loads(r.text)

def get_waste_types(ort):
    r = requests.get(f"https://www.awsh.de/api_v2/collection_dates/1/ort/{ort}/abfallarten")
    return json.loads(r.text)

def main():
    ortsnummer = None
    strassennummer = None
    abfallarten = []

    cities = get_cities()
    choices = []
    for d in cities["orte"]:
            value = {
                "ortsnummer": d["ortsnummer"],
                "ortsbezeichnung": d["ortsbezeichnung"],
                "plz": d["plz"],
            }
            choices.append(
                (
                    f"{d['plz']} {d['ortsbezeichnung']}",
                    value,
                )
            )
    questions = [inquirer.List("city", choices=choices, message="Select City")]
    answers = inquirer.prompt(questions)
    ortsnummer = answers["city"]["ortsnummer"]
    strassen = get_strassen(ortsnummer)
    choices.clear()

    for d in strassen["strassen"]:
            value = {
                "strassennummer": d["strassennummer"],
                "strassenbezeichnung": d["strassenbezeichnung"],
            }
            choices.append(
                (
                    f"{d['strassennummer']} {d['strassenbezeichnung']}",
                    value,
                )
            )
    
    questions = [inquirer.List("address", choices=choices, message="Select address")]
    answers = inquirer.prompt(questions)
    strassennummer = answers["address"]["strassennummer"]
    waste_types = get_waste_types(ortsnummer)
    choices.clear()

    for d in waste_types["abfallarten"]:
            value = {
                "bezeichnung": d["bezeichnung"],
                "zyklus": d["zyklus"],
                "id": d["id"],
            }
            choices.append(
                (
                    f"{d['bezeichnung']} {d['zyklus']}",
                    value,
                )
            )
    
    questions = [inquirer.Checkbox("wastetypes", choices=choices, message="Select Types")]
    answers = inquirer.prompt(questions)
    for d in answers["wastetypes"]:
        abfallarten.append(d["id"])

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: awsh")
    print("      args:")
    print(f"        ortId: {ortsnummer}")
    print(f"        strId: {strassennummer}")
    for d in abfallarten:
        print(f"        waste_types: - {d}")

if __name__ == "__main__":
    main()