#!/usr/bin/env python3

import requests
from datetime import datetime

API_URL = "https://www.narabtomningskalender.se/basfiler/system_ladda_adresser.php"


def parse_address_list(text: str):
    addresses = []
    for line in text.strip().splitlines():
        parts = line.split("|")
        if len(parts) != 5:
            print(f"Malformed line: {line}")
            return []
        hsG, hsO, knR, abK, nrA = [p.strip() for p in parts]
        addresses.append({
            "hsG": hsG,
            "hsO": hsO,
            "knR": knR,
            "abK": abK,
            "nrA": nrA
        })
    return addresses


address = input("Enter your address: ")

params = {
    "svar": address,
    "limit": "500",
    "timestamp": str(int(datetime.now().timestamp() * 1000))
}

# get address data
r = requests.get(API_URL, params=params)

addresses = parse_address_list(r.text)
suggestions = [addr["hsG"] + " " + addr["hsO"] +
               (" (Verksamhet)" if addr["abK"] == "VERKSAMHET" else "") +
               (" (Flerfamilj)" if addr["abK"]
                == "FLERFAMILJ" else "") + " kundNr: "+addr["knR"]
               for addr in addresses]

for addr in suggestions:
    print(addr)
