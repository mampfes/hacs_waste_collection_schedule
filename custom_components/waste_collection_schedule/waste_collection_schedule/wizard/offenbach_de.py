#!/usr/bin/env python3

import re
import site
import inquirer
import requests
import traceback

s = requests.Session()

def get_streets(answers):
    url = "https://www.insert-it.de/BmsAbfallkalenderOffenbach/Main/GetStreets"
    params = { "text": answers['street'], 
                "filter%5Bfilters%5D%5B0%5D%5Bvalue%5D": answers['street'],
                "filter%5Bfilters%5D%5B0%5D%5Bfield%5D": "Name", 
                "filter%5Bfilters%5D%5B0%5D%5Boperator%5D": "contains", 
                "filter%5Bfilters%5D%5B0%5D%5BignoreCase%5D": "true", 
                "filter%5Blogic%5D": "and" } 

    r = s.get(url, params=params)
    r.raise_for_status()

    return r.json()

def get_numbers(streetname, jdata):
    url = "https://www.insert-it.de/BmsAbfallkalenderOffenbach/Main/GetLocations"

    streetId = [ i['ID'] for i in jdata if i['Name'] == streetname] [0]
    params = { 
        "streetId": streetId,
        "filter[filters][0][field]": "ID",
        "filter[filters][0][operator]": "eq",
        "filter[filters][0][value]": streetId,
        "filter[logic]": "and"
    }

    r = s.get(url, params=params)
    r.raise_for_status()

    return r.json()


def main():
    questions = [inquirer.Text("street", message="Enter search string for street")]
    
    jdata = []

    while not len(jdata):
        try:
            answers = inquirer.prompt(questions)
            jdata = get_streets(answers)
        except Exception as e:
            traceback.print_exc()
            sys.exit()

    questions = [
            inquirer.List(
                "streetname", choices=[i['Name'] for i in jdata], message="Select street"
            )
        ]

    try:
        answers = inquirer.prompt(questions)
        jdata = get_numbers(**answers, jdata=jdata)
    except Exception as e:
            traceback.print_exc()
            sys.exit()

    questions = [
            inquirer.List(
                "streetnumber", choices=[i['Text'] for i in jdata], message="Select number"
            )
        ]
    answers = inquirer.prompt(questions)
    location_id =  [ i['ID'] for i in jdata if i['Text'] == answers['streetnumber']][0]

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: offenbach_de")
    print("      args:")
    print(f"        f_id_location: {location_id}")
    

if __name__ == "__main__":
    main()