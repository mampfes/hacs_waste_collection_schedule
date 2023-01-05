from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Ximmio"
DESCRIPTION = "Source for Ximmio B.V. waste collection."
URL = "https://www.ximmio.nl"


def EXTRA_INFO():
    return [{"title": s["title"], "url": s["url"]} for s in SERVICE_MAP]


TEST_CASES = {
    "ACV Group": {"company": "acv", "post_code": "6721MH", "house_number": 1},
    "Meerlanden": {"company": "meerlanden", "post_code": "1435BX", "house_number": 650},
    "Almere": {"company": "almere", "post_code": "1318NG", "house_number": 15},
}


SERVICE_URLS = {
    "avalex": "https://wasteprod2api.ximmio.com",
    "meerlanden": "https://wasteprod2api.ximmio.com",
    "rad": "https://wasteprod2api.ximmio.com",
    "westland": "https://wasteprod2api.ximmio.com",
}

SERVICE_MAP = [
    {
        "title": "ACV Group",
        "url": "https://www.acv-afvalkalender.nl/",
        "uuid": "f8e2844a-095e-48f9-9f98-71fceb51d2c3",
        "company": "acv",
    },
    {
        "title": "Gemeente Almere",
        "url": "https://www.almere.nl/",
        "uuid": "53d8db94-7945-42fd-9742-9bbc71dbe4c1",
        "company": "almere",
    },
    {
        "title": "Area Afval",
        "url": "https://www.area-afval.nl/",
        "uuid": "adc418da-d19b-11e5-ab30-625662870761",
        "company": "areareiniging",
    },
    {
        "title": "Avalex",
        "url": "https://www.avalex.nl/",
        "uuid": "f7a74ad1-fdbf-4a43-9f91-44644f4d4222",
        "company": "avalex",
    },
    {
        "title": "Avri",
        "url": "https://www.avri.nl/",
        "uuid": "78cd4156-394b-413d-8936-d407e334559a",
        "company": "avri",
    },
    {
        "title": "Bar Afvalbeheer",
        "url": "https://www.bar-afvalbeheer.nl/",
        "uuid": "bb58e633-de14-4b2a-9941-5bc419f1c4b0",
        "company": "bar",
    },
    {
        "title": "Gemeente Hellendoorn",
        "url": "https://www.hellendoorn.nl/",
        "uuid": "24434f5b-7244-412b-9306-3a2bd1e22bc1",
        "company": "hellendoorn",
    },
    {
        "title": "Meerlanden",
        "url": "https://meerlanden.nl/",
        "uuid": "800bf8d7-6dd1-4490-ba9d-b419d6dc8a45",
        "company": "meerlanden",
    },
    {
        "title": "Gemeente Meppel",
        "url": "https://www.meppel.nl/",
        "uuid": "b7a594c7-2490-4413-88f9-94749a3ec62a",
        "company": "meppel",
    },
    {
        "title": "RAD BV",
        "url": "https://www.radbv.nl",
        "uuid": "13a2cad9-36d0-4b01-b877-efcb421a864d",
        "company": "rad",
    },
    {
        "title": "Reinis",
        "url": "https://www.reinis.nl/",
        "uuid": "9dc25c8a-175a-4a41-b7a1-83f237a80b77",
        "company": "reinis",
    },
    {
        "title": "Twente Milieu",
        "url": "https://www.twentemilieu.nl/",
        "uuid": "8d97bb56-5afd-4cbc-a651-b4f7314264b4",
        "company": "twentemilieu",
    },
    {
        "title": "Waardlanden",
        "url": "https://www.waardlanden.nl/",
        "uuid": "942abcf6-3775-400d-ae5d-7380d728b23c",
        "company": "waardlanden",
    },
    {
        "title": "Gemeente Westland",
        "url": "https://www.gemeentewestland.nl/",
        "uuid": "6fc75608-126a-4a50-9241-a002ce8c8a6c",
        "company": "westland",
    },
]


def get_service_name_map():
    return {s["company"]: s["uuid"] for s in SERVICE_MAP}


class Source:
    def __init__(self, company, post_code, house_number):
        self._post_code = post_code
        self._house_number = house_number
        self._url = SERVICE_URLS.get(company, "https://wasteapi.ximmio.com")
        self._company_code = get_service_name_map()[company]

    def fetch(self):
        data = {
            "postCode": self._post_code,
            "houseNumber": self._house_number,
            "companyCode": self._company_code,
        }
        r = requests.post(f"{self._url}/api/FetchAdress", data=data)
        d = r.json()

        dataList = d["dataList"][0]
        data = {
            "uniqueAddressID": dataList["UniqueId"],
            "startDate": datetime.now().strftime("%Y-%m-%d"),
            "endDate": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "companyCode": self._company_code,
            "community": dataList.get("Community", ""),
        }
        r = requests.post(f"{self._url}/api/GetCalendar", data=data)
        d = r.json()

        entries = []
        for wasteType in d["dataList"]:
            for date in wasteType["pickupDates"]:
                entries.append(
                    Collection(
                        date=datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").date(),
                        t=wasteType["_pickupTypeText"],
                    )
                )
        return entries
