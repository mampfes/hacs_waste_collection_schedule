#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

API_URL = "https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.wokingham.gov.uk",
    "Origin": "https://www.wokingham.gov.uk",
    "Referer": "https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day",
}

s = requests.Session()

postcode = input("Enter your postcode: ")
postcode = "".join(postcode.upper().strip().replace(" ", ""))

r = s.get(API_URL)
soup = BeautifulSoup(r.text, "html.parser")
x = soup.find("input", {"name": "form_build_id"})
form_id = x.get("value")

payload = {
    "postcode_search": postcode,
    "op": "Find Address",
    "form_build_id": form_id,
    "form_id": "waste_collection_api_form",
}

r = s.post(
    API_URL,
    headers=HEADERS,
    data=payload,
)

soup = BeautifulSoup(r.text, "html.parser")
dropdown = soup.find("div", {"class": "form-item__dropdown"})
addresses = dropdown.find_all("option")
for item in addresses:
    print(item.get("value"), "=", item.text.title().replace(",", ""))
