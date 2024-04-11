from urllib.parse import urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "FCC Environment"
DESCRIPTION = """
    Consolidated source for waste collection services for ~60 local authorities.
    Currently supports:
    West Devon (Generic Provider)
    South Hams (Generic Provider)
    Market Harborough (Custom Provider)
    """
URL = "https://fccenvironment.co.uk"
EXTRA_INFO = [
    {"title": "Harborough District Council", "url": "https://harborough.gov.uk"},
    {"title": "South Hams District Council", "url": "https://southhams.gov.uk/"},
    {"title": "West Devon Borough Council", "url": "https://www.westdevon.gov.uk/"},
]

TEST_CASES = {
    "14_LE16_9QX": {"uprn": "100030491624"},  # region omitted to test default values
    "4_LE16_9QX": {"uprn": "100030491614", "region": "harborough"},
    "16_LE16_7NA": {"uprn": "100030493289", "region": "harborough"},
    "10_LE16_8ER": {"uprn": "200001136341", "region": "harborough"},
    "9_PL20_7SH": {"uprn": "10001326315", "region": "westdevon"},
    "3_PL20_7RY": {"uprn": "10001326041", "region": "westdevon"},
    "2_PL21_9BN": {"uprn": "100040279446", "region": "southhams"},
    "4_SL21_0HZ": {"uprn": "100040281987", "region": "southhams"},
}

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
}


class Source:
    def __init__(self, uprn: str, region: str = "harborough") -> None:
        self.uprn = uprn
        self.region = region

    def getcollectiondetails(self, endpoint: str) -> list[Collection]:
        domain = urlparse(endpoint).netloc
        session = requests.Session()
        cookies = session.get(f"https://{domain}/", verify=False)
        response = session.post(
            endpoint,
            headers={
                "x-requested-with": "XMLHttpRequest",
            },
            data={
                "fcc_session_token": cookies.cookies["fcc_session_cookie"],
                "uprn": self.uprn,
            },
            verify=False,
        )
        results = {}
        for item in response.json()["binCollections"]["tile"]:
            try:
                soup = BeautifulSoup(item[0], "html.parser")
                date = parser.parse(soup.find_all("b")[2].text.split(",")[1].strip()).date()
                service = soup.text.split("\n")[0]
            except parser._parser.ParserError:
                continue

            """
            Handle duplication before creating the list of Collections
            """
            for type in ICON_MAP:
                if type in service:
                    if type in results.keys():
                        if date < results[type]:
                            results[type] = date
                    else:
                        results[type] = date

        entries = []
        for result in results:
            entries.append(
                Collection(
                    date=results[result],
                    t=result,
                    icon=ICON_MAP.get(result),
                )
            )
        return entries

    def harborough(self) -> list[Collection]:
        _icons = {
            "NON-RECYCLABLE WASTE BIN COLLECTION": "mdi:trash-can",
            "RECYCLING COLLECTION": "mdi:recycle",
            "GARDEN WASTE COLLECTION": "mdi:leaf",
        }  # Custom icons to avoid a breaking change
        r = requests.post(
            "https://harborough.fccenvironment.co.uk/detail-address",
            data={"Uprn": self.uprn},
            verify=False,
        )
        soup = BeautifulSoup(r.text, "html.parser")
        services = soup.find(
            "div",
            attrs={"class": "blocks block-your-next-scheduled-bin-collection-days"},
        ).find_all("li")
        entries = []
        for service in services:
            for type in _icons:
                if type.lower() in service.text.lower():
                    try:
                        date = parser.parse(service.find("span", attrs={"class": "pull-right"}).text.strip()).date()
                    except parser._parser.ParserError:
                        continue

                    entries.append(
                        Collection(
                            date=date,
                            t=type,
                            icon=_icons[type.upper()],
                        )
                    )
        return entries

    def fetch(self) -> list[Collection]:
        if self.region == "harborough":
            return self.harborough()
        elif self.region == "westdevon":
            return self.getcollectiondetails(
                endpoint="https://westdevon.fccenvironment.co.uk/ajaxprocessor/getcollectiondetails"
            )
        elif self.region == "southhams":
            return self.getcollectiondetails(
                endpoint="https://waste.southhams.gov.uk/mycollections/getcollectiondetails"
            )
