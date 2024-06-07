import json
import re
from datetime import datetime, timedelta, date

import requests
from waste_collection_schedule import Collection

TITLE = "Town of Victoria Park"
DESCRIPTION = "Source for www.victoriapark.wa.gov.au Waste Collection Services"
URL = "https://www.victoriapark.wa.gov.au"
TEST_CASES = {
    "Monday": {"address": "51 Cookham Road, Lathlain"}, # Monday
    "Town of Vic Park (Tues)": {
        "address": "99 Shepperton Road, VICTORIA PARK",
        "predict": True,
    },  # Tuesday
    "Wednesday": {"address": "156 Oats St, Carlisle"}, # Wednesday
    "Park Centre (Thurs)": {"address": "789 Albany hwy, EAST VICTORIA PARK"},  # Thursday
    "Aqualife (Thurs)": {"address": "42 Somerset St, East Victoria Park"}, # Thursday
    "Friday": {
        "address": "90 Canterbury Terrace, East Victoria Park",
        "predict":  True 
    } # Friday
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
    "Go Bin": "mdi:leaf",
}

def clean_months( start_date, date_str ):
    date_cleaned = start_date + re.sub('^\d+', '', date_str)
    date_cleaned = re.sub('Janu?a?r?y?', 'Jan', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Febr?u?a?r?y?', 'Feb', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Marc?h?', 'Mar', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Apri?l?', 'Apr', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('June?', 'Jun', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('July?', 'Jul', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Augu?s?t?', 'Aug', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Sept?e?m?b?e?r?', 'Sep', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Octo?b?e?r?', 'Oct', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Nov?e?m?b?e?r?', 'Nov', date_cleaned, flags=re.IGNORECASE)
    date_cleaned = re.sub('Dec?e?m?b?e?r?', 'Dec', date_cleaned, flags=re.IGNORECASE)
    return date_cleaned


class Source:
    def __init__(self, address, predict=False):
        address = address.strip()
        # print (address)
        address = re.sub(" +", " ", address)
        address = re.sub("hwy", "highway", address, flags=re.IGNORECASE)
        address = re.sub(r"western australia (\d{4})", "WA \\1", address, flags=re.IGNORECASE)
        address = re.sub(r" wa (\d{4})", "  WA  \\1", address, flags=re.IGNORECASE)
        self._address = address
        if type(predict) != bool:
            raise Exception("'predict' must be a boolean value")
        self._predict = predict

    def collect_dates(self, start_date, weeks):
        dates = []
        dates.append(start_date)
        for i in range (1, int(4/weeks)):
            start_date = start_date + timedelta(days=(weeks*7))
            dates.append(start_date)
        return dates

    def fetch(self):
        entries = []
        # initiate a session
        url = "https://maps.vicpark.wa.gov.au/IntraMaps22B/ApplicationEngine/Integration/api/search"

        payload = {}
        params = {
            "configId": "00000000-0000-0000-0000-000000000000",
            "form": "4a7d4da6-26b5-40ce-a0b3-814f5e82c0f3",
            "fields": self._address,
        }
        headers = {
            "Authorization": "apikey 8b1fdca5-5d16-4724-99cd-df3a32c650a0"
        }

        r = requests.get(url, headers=headers, data=payload, params=params)
        r.raise_for_status()
        # sessionid = r.headers["X-IntraMaps-Session"]

        j = r.json()

        # print ('json 1 ')
        # print (j)

        if len(j) == 0:
            raise Exception("address not found")

        j = j[0]


        # Just picking first date
        # if len(j) > 1:
        #     raise Exception("multiple addresses found")

        # search for the address
        url = "https://maps.vicpark.wa.gov.au/IntraMaps22B/ApplicationEngine/Integration/api/search"

        # payload = json.dumps({"fields": [self._address]})
        fields_dict = {item['name']: item['value'] for item in j}

        # print ('fields ')
        # print (fields_dict.get("mapkey") + ',' + fields_dict.get("dbkey"))

        params = {
            "configId": "00000000-0000-0000-0000-000000000000",
            "form": "f3f264a3-94f5-499a-a697-0fac668cd027",
            "fields": fields_dict.get("mapkey") + ',' + fields_dict.get("dbkey")
        }

        r = requests.get(url, headers=headers, data=payload, params=params)
        r.raise_for_status()

        fields_json = r.json()[0]
        # print ('json 2 ')
        # print (fields_json)

        data_dict = {item['name']: item for item in fields_json}

        day_rubbish = data_dict.get('General_Bin')["value"].split(" - ")[0]
        date_recycling = data_dict.get('Recycling_Bin')["value"][:11]
        date_go = data_dict.get('GO_Bin')["value"][:11]
        raw_green_waste = data_dict.get('Green_Waste')["value"]
        raw_bulk_waste = data_dict.get('Bulk_Waste')["value"]
        # 15-16 Jul 2023, 9-10 Dec 2023
        # Months are inconsistent and a range
        green_waste_bits = re.split(r'\s*[\-,()]\s*', raw_green_waste)
        date_green_waste = clean_months(green_waste_bits[0], green_waste_bits[1])
        date_green_waste2 = clean_months(green_waste_bits[2], green_waste_bits[3])

        bulk_waste_bits = re.split(r'\s*[\-,()]\s*', raw_bulk_waste)
        date_bulk_waste = clean_months(bulk_waste_bits[0], bulk_waste_bits[1])
        date_bulk_waste2 = clean_months(bulk_waste_bits[2], bulk_waste_bits[3])
         
        date_rubbish = datetime.today() + timedelta(days=-1)
        while date_rubbish.strftime("%A").lower() != day_rubbish.lower():
            date_rubbish = date_rubbish + timedelta(days=1)

        if self._predict:
            rub_dates = self.collect_dates(date_rubbish.date(), 1)
            rec_dates = self.collect_dates(datetime.strptime(date_recycling, "%d %b %Y").date(), 2)
            go_dates = self.collect_dates(datetime.strptime(date_go, "%d %b %Y").date(), 2)
            grn_dates = [
                datetime.strptime(date_green_waste, "%d %b %Y").date(),
                datetime.strptime(date_green_waste2, "%d %b %Y").date()
                ]
            blk_dates = [
                datetime.strptime(date_bulk_waste, "%d %b %Y").date(),
                datetime.strptime(date_bulk_waste2, "%d %b %Y").date()
                ]
        else:
            rub_dates = [date_rubbish.date()]
            rec_dates = [datetime.strptime(date_recycling, "%d %b %Y").date()]
            go_dates = [datetime.strptime(date_go, "%d %b %Y").date()]
            grn_dates = [datetime.strptime(date_green_waste, "%d %b %Y").date()]
            blk_dates = [datetime.strptime(date_bulk_waste, "%d %b %Y").date()]
        
        collections = []
        collections.append({"type": "Rubbish", "dates": rub_dates})
        collections.append({"type": "Recycling", "dates": rec_dates})
        collections.append({"type": "Go Bin", "dates": go_dates})
        collections.append({"type": "Green Waste", "dates": grn_dates})
        collections.append({"type": "Bulk Waste", "dates": blk_dates})
        
        for collection in collections:
            for date in collection["dates"]:
                entries.append(
                    Collection(
                        date=date,
                        t=collection["type"],
                        icon = ICON_MAP.get(collection["type"]),
                    )
                )

        return entries
