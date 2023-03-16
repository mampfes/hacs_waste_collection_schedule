import urllib.parse
from alive_progress import alive_bar
import time
import requests
from bs4 import BeautifulSoup
#import threading
import sys
from requests.exceptions import HTTPError
from http import HTTPStatus
import argparse

TITLE = "Samverkan Återvinning Miljö (SÅM)"
DESCRIPTION = "Source script for samiljo.se"
URL = "https://www.samiljo.se"

"""requirements
alive_progress
beautifulsoup4
requests
urllib3
"""


# Will take arguments --city, --street, and --char
parser = argparse.ArgumentParser(description="Searches for new bin types not yet included in NAME_MAP. Searches all addresses in the database if not otherwise specified.")
parser.add_argument("--street", type=str, help="Specify a street adress or part of it.")
parser.add_argument("--city", type=str, help="Specify a city.")
parser.add_argument("--char", type=str, help="exclude characters from search (eg \"abcdef\")")
args = parser.parse_args()

API_URLS = {
    "address_search": "https://webbservice.indecta.se/kunder/sam/kalender/basfiler/laddaadresser.php",
    "collection": "https://webbservice.indecta.se/kunder/sam/kalender/basfiler/onlinekalender.php",
}

NAME_MAP = {
    "HKARL1": "Fyrfackskärl 1",  # Matavfall, Restavfall, Tidningar & Färgat glas
    "HKARL1-H": "Fyrfackskärl 1 - Helgvecka", # Matavfall, Restavfall, Tidningar & Färgat glas
    "HKARL2": "Fyrfackskärl 2", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "HKARL2-H": "Fyrfackskärl 2 - Helgvecka", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "HMAT": "Matavfall",
    "HMAT-H": "Matavfall - Helgvecka",
    "HREST": "Restavfall",
    "HREST-H": "Restavfall - Helgvecka",
    "HOSORT": "Blandat Mat- och Restavfall",
    "HOSORT-H": "Blandat Mat- och Restavfall - Helgvecka",
    "FKARL1": "Fyrfackskärl 1",  # Matavfall, Restavfall, Tidningar & Färgat glas
    "FKARL2": "Fyrfackskärl 2", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "FKARL1-H": "Fyrfackskärl 1 - Helgvecka", # Matavfall, Restavfall, Tidningar & Färgat glas
    "FKARL2-H": "Fyrfackskärl 2 - Helgvecka", # Förpackningar av Papper, Plast & Metall samt Ofärgat glas
    "FOSORT": "Blandat Mat- och Restavfall",
    "FOSORT-H": "Blandat Mat- och Restavfall - Helgvecka",
    "HREST-HK": "Restavfall med Hemkompost",
    "HREST-HK-H": "Restavfall med Hemkompost - Helgvecka",
    "HKARL1-HK": "Fyrfackskärl 1 med Hemkompost",  # Restavfall, Tidningar & Färgat glas
    "HKARL1-HK-H": "Fyrfackskärl 1 med Hemkompost - Helgvecka",  # Restavfall, Tidningar & Färgat glas
    "TRG": "Trädgårdskärl",
    "TRG-H": "Trädgårdskärl - Helgvecka",
    "FREST-HK": "Restavfall med Hemkompost",
    "FREST-HK-H": "Restavfall med Hemkompost - Helgvecka",
    "FKARL1-HK-H": "Fyrfackskärl 1 med Hemkompost",
    "FKARL1-HK": "Fyrfackskärl 1 med Hemkompost - Helgvecka",
    "FREST": "Restavfall",
    "FREST-H": "Restavfall - Helgvecka",
}

retries = 3
retry_codes = [
    HTTPStatus.TOO_MANY_REQUESTS,
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.SERVICE_UNAVAILABLE,
    HTTPStatus.GATEWAY_TIMEOUT,
]


NEW_NAME_MAP = {}

def waste_searcher(arg1):  # sourcery skip: use-fstring-for-concatenation
            #sema.acquire()
            new_type = ""
            array = arg1.split("|")
            street=array[0]
            city=array[1]
            A=array[-1]
            payload={"hsG": street, "hsO": city, "nrA": A}
            payload_str=urllib.parse.urlencode(payload, encoding="cp1252")
            # request for the wasteschedule
            for n in range(retries):
                try:
                    wasteschedule=requests.get(
                        API_URLS["collection"], params=payload_str)
                    wasteschedule.raise_for_status()

                    break

                except HTTPError as exc:
                    code = exc.wasteschedule.status_code
        
                    if code in retry_codes:
                        # retry after n seconds
                        time.sleep(n)
                        continue

                    raise

            """ wasteschedule=requests.get(
                API_URLS["collection"], params=payload_str)
            wasteschedule.raise_for_status() """

            soup=BeautifulSoup(wasteschedule.text, "html.parser")

            # Calender uses diffrent tags for the last week of the month
            wastedays=soup.find_all(
                "td", {"style": "styleDayHit"}) + soup.find_all("td", "styleDayHit")

            # get a list of all tags with waste collection days for the current year
            for wasteday in wastedays:
                wasteday_wastetype=wasteday.parent.parent
                # list of bins collected for given day
                for td in wasteday_wastetype.contents[3].find_all("td"):
                    if td.has_attr("class"):
                        waste=str(td.get_attribute_list("class")).strip(" []/'")
                        if waste not in NAME_MAP and waste not in NEW_NAME_MAP:
                            new_type=waste + "|" + street + "|" + city
                            NEW_NAME_MAP[waste]=(new_type)
            del soup, wasteschedule, wastedays, wasteday_wastetype
            bar()
            #sema.release()
            return

#input any character alredy searched
#used_char = ["a", "b",]
used_char = []
checked_addresses = []
alphabet = "abcdefghijklmnopqrstuvwxyzåäö"

if args.street or args.city:
    used_char = []
elif args.used_char:
    used_char = list(args.char)

bar_count = len(alphabet) # - len(used_char)

with alive_bar(bar_count) as bar:
    for char in alphabet:
            if not used_char: 
                #if no used characters add a addresslist to checked list without check aggainst checked_list
                adresslist = requests.get(
                    API_URLS["address_search"], params={"svar": "a"}
                )
                checked_addresses=adresslist.text.lower().splitlines()
                alphabet = "".join(alphabet.split("a", 1))

            else:
                adresslist=requests.get(
                    API_URLS["address_search"], params={"svar": char}
                )
                adresslist.raise_for_status()
                new_addressarray=adresslist.text.lower().splitlines()
                for line in new_addressarray: 
                    # if line contains an alredy searched character then don"t write it
                    found_char = 0
                    for x in used_char:
                        if x in line.strip("\n"): 
                            found_char = 1
                    if found_char == 0: 
                        checked_addresses.append(line)
                #add searched character to used_char
                used_char.append(char)
            bar()



checked_addresses2 = []
if args.city and args.street:
            checked_addresses2.extend(
                line for line in checked_addresses
                if args.city.lower() in line and args.street.lower() in line)
            checked_addresses = checked_addresses2
elif args.street:
            checked_addresses2.extend(line for line in checked_addresses
                                      if args.street.lower() in line)
            checked_addresses = checked_addresses2
elif args.city:
            checked_addresses2.extend(line for line in checked_addresses
                                      if args.city.lower() in line)
            checked_addresses = checked_addresses2

total = len(checked_addresses)

with alive_bar(total) as bar:
    for line in checked_addresses:
            waste_searcher(line)

""" threads_list = []
maxthreads = 10
sema = threading.Semaphore(value=maxthreads)
with alive_bar(total) as bar:
    for line in checked_addresses:
            t = threading.Thread(target=waste_searcher, args=[line])
            t.start()
            threads_list.append(t) """


""" for thread in threads_list:
    thread.join() """

if NEW_NAME_MAP:
            for line in NEW_NAME_MAP.values():
                  print(line)
            print("Map these new waste types to a common name using https://samiljo.se/avfallshamtning/hamtningskalender in conjunction with addresses above. Add the new common name to the NAME_MAP in samiljo_se.py and Samiljo_se_wastetype_searcher.py")
elif args.city and args.street:
            print(
                f"The waste types for {args.street}, {args.city} are alredy included in the NAME_MAP."
            )
else:
            print("Found no new waste types.")