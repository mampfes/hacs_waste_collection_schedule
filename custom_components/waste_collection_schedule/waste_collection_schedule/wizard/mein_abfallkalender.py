#!/usr/bin/env python3
import inquirer
import requests
import string
import random
import re

from bs4 import BeautifulSoup

URL_BASE = "https://{city_name}.mein-abfallkalender.de/app/webcal.html"
s = requests.Session()

def get_waste_type(data):
    soup = BeautifulSoup(data, features="html.parser")

    fieldsets = soup.find_all("fieldset", { "data-role": "controlgroup"})

    for i in fieldsets:
        if not "<legend>Abfallarten" in str(i):
            continue
        ret = {}
        for label in i.find_all("label"):
            ret[label.text] = label['for'].split("-")[1]
        return ret
    return {}


def get_street_ids(data):
    soup = BeautifulSoup(data, features="html.parser")
    strs = soup.find("select", { "name": "street_id"}).find_all("option")
    return [ ( s['value'], s.text) for s in strs]


def get_download_link (city, street_id, waste_types, user_email):
        waste_type_str = "&".join([ f"filter_waste={s}" for s in waste_types ])
        url = "https://{city}.mein-abfallkalender.de/app/webcal.html?street_id={street_id}&filter_period=next_1000&filter_time_delta=noalarm&filter_usage=ical_download&{waste_type_str}&user_email={user_email}&user_email_confirm={user_email}&user_dsgvo=1".format(city=city, street_id=street_id, waste_type_str=waste_type_str, user_email=user_email)

        r = s.get(url)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        for a in soup.find_all("a"):
            if "ical.ics" in a['href']:
                return a['href']
        return None


def get_random_email(domain):
    result_str = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    return f"{result_str}@{domain}"

def normalize (s):
    charmap = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe'}
    return s.casefold().translate(charmap)

def main():

    city = inquirer.prompt([inquirer.Text("city", message="Enter the name of the city")])
    r = s.get(URL_BASE.format(city_name=city['city']))
    r.raise_for_status()

    waste_type = get_waste_type(r.text)
    streets = get_street_ids(r.text)

    
    street_name = inquirer.prompt([inquirer.Text("street_name", message="Enter the name of the street")])
    filtered_streets = [o[1] for o in list(filter(lambda x: normalize(street_name['street_name']) in normalize(x[1]), streets))]
    street = inquirer.prompt([inquirer.List("street", choices=filtered_streets, message="Select a street")])
    location = [ st[0] for st in streets if st[1] == street['street'] ][0]


    answers = inquirer.prompt([inquirer.Checkbox('waste_type',
                    message="Type of waste",
                    choices=waste_type.keys(),
                    )])


    dwn = get_download_link(city['city'], location, answers['waste_type'], get_random_email("test.com"))
    m = re.search(r'cid=(\d+)', dwn)
    
    cid = m.group(1) if m else -1

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: mein_abfallkalender")
    print("      args:")
    print(f"        city: {city['city']}")
    print(f"        street_id: {location}")
    print(f"        cid: {cid}")
    print(f"        user_email: test@test.com")
    print("        waste_types:")
    print("\n".join([f"          - {waste_type.get(wt)} ## {wt}" for wt in answers['waste_type']]))

if __name__ == "__main__":
    main()

