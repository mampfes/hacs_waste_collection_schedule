#!/usr/bin/env python3

import inquirer
import requests

ENDPOINT_STREET = "https://umnewforms.bsr.de/p/de.bsr.adressen.app/streetNames"
ENDPOINT_SCHEDID = "https://umnewforms.bsr.de/p/de.bsr.adressen.app/plzSet/plzSet"

def main():

    while True:
        questions = [inquirer.Text("street", message="Enter search string for street")]
        answers = inquirer.prompt(questions)
        args = {
            "searchQuery": answers["street"]
        }

        with requests.Session() as street_session:
            response = street_session.get(ENDPOINT_STREET, params=args)
        street_list = response.json()
        if len(street_list) == 0:
            print("Search returned no result. Please try again.")
            continue

        if len(street_list) == 1:
            street = street_list[0]["value"]
        else:
            street_choices = [entry["value"] for entry in street_list]
            # select street
            questions = [
                inquirer.List("street", choices=street_choices, message="Select street")
            ]
            answers = inquirer.prompt(questions)
            street = answers["street"]
        print(f"Selected street: {street}.")

        questions = [inquirer.Text("number", message="Enter house number")]
        answers = inquirer.prompt(questions)
        number = answers['number']
        print(f"Selected number: {number}.")
        args = {
            "searchQuery": f"{street}:::{number}"
        }
        with requests.Session() as schedid_session:
            response = schedid_session.get(ENDPOINT_SCHEDID, params=args)
        schedid_list = response.json()
        if len(schedid_list) == 0:
            print("Search returned no result. Please try again.")
            continue
        if len(schedid_list) == 1:
            schedid = schedid_list[0]["value"]
            address = schedid_list[0]["label"]
        if len(schedid_list) > 1:
            schedid_choices = [entry["label"] for entry in schedid_list]
            questions = [inquirer.List("address", choices=schedid_choices, message="Select your address")]
            answers = inquirer.prompt(questions)
            address = answers["address"]
            for entry in schedid_list:
                if entry["label"] == address:
                    schedid = entry["value"]
                    break
        print(f"Selected address: {address}.")
        print(f"Schedule id for this address: {schedid}.")
        questions = [inquirer.Confirm("confirm", message="Is the address correct?", default=True)]
        answers = inquirer.prompt(questions)
        if not answers["confirm"]:
            print("Please try again.")
            continue
        break

    print("\nCopy the following snippet into your configuration.yaml:")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: bsr_de")
    print("      args:")
    print(f"        schedule_id: \"{schedid}\"")


if __name__ == "__main__":
    main()
