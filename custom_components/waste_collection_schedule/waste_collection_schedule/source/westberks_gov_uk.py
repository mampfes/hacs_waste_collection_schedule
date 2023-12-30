import json
import time
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "West Berkshire Council"
DESCRIPTION = "Source for westberks.gov.uk services for West Berkshire Council"
URL = "https://westberks.gov.uk"
TEST_CASES = {
    "known_uprn": {"uprn": "100080241094"},
    "known_uprn as number": {"uprn": 100081026602},
    "unknown_uprn_by_name": {
        "postcode": "RG7 6NZ",
        "housenumberorname": "PARROG HOUSE",
    },
    "unknown_uprn_by_number": {"postcode": "RG18 4QU", "housenumberorname": "6"},
    "unknown_uprn_business": {"postcode": "RG18 4GE", "housenumberorname": "3"},
}

ICON_MAP = {
    "RUBBISH": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
}

SEARCH_URLS = {
    "uprn_search": "https://www.westberks.gov.uk/apiserver/ajaxlibrary",
    "collection_search": "https://www.westberks.gov.uk/apiserver/ajaxlibrary",
}

COLLECTIONS = {"Rubbish", "Recycling"}


def fix_date(d: date):
    if datetime.now().month == 12 and d.month in (1, 2):
        d = d.replace(year=d.year + 1)
    return d


class Source:
    def __init__(
        self, uprn=None, postcode=None, housenumberorname=None
    ):  # argX correspond to the args dict in the source configuration
        self._uprn = str(uprn).zfill(12) if uprn is not None else None
        self._postcode = postcode
        self._housenumberorname = housenumberorname

    def fetch(self):
        entries = []
        session = requests.Session()

        # Find the UPRN based on the postcode and the property name/number
        if self._uprn is None:
            self._postcode = self._postcode.strip()
            jsonrpc = {
                "id": str(int(time.time())),
                "method": "location.westberks.echoPostcodeFinder",
                "params": {"provider": "", "postcode": self._postcode},
            }
            args = {"callback": "HomeAssistant", "jsonrpc": json.dumps(jsonrpc), "_": 0}
            r = requests.get(SEARCH_URLS["uprn_search"], params=args)

            # I don't really know python so there *must* be a better way to do these four lines!
            response_str = r.content.decode("utf-8")
            data_length = len(response_str) - 1
            response_sub = response_str[14:data_length]
            address_data = json.loads(response_sub)

            propertyUprns = address_data["result"]
            for match in propertyUprns:
                if match["line1"].startswith(self._housenumberorname):
                    self._uprn = match["udprn"]
                if match["buildingnumber"].startswith(
                    self._housenumberorname
                ):  # no evidence (yet) that their database uses this
                    self._uprn = match["udprn"]

        entries = []

        # Get the collection days based on the UPRN (either supplied through arguments or searched for above)
        if self._uprn is not None:
            # POST request - one for each type as it is a separate method in the api
            rubbish_args = {
                "jsonrpc": "2.0",
                "id": str(int(time.time())),
                "method": "goss.echo.westberks.forms.getNextRubbishCollectionDate",
                "params": {"uprn": self._uprn},
            }
            recycling_args = {
                "jsonrpc": "2.0",
                "id": str(int(time.time())),
                "method": "goss.echo.westberks.forms.getNextRecyclingCollectionDate",
                "params": {"uprn": self._uprn},
            }
            r = session.post(SEARCH_URLS["collection_search"], json=rubbish_args)
            rubbish_data = json.loads(r.content)
            r = session.post(SEARCH_URLS["collection_search"], json=recycling_args)
            recycling_data = json.loads(r.content)

            # if subtext is empty, use datetext
            # if both have values, use subtext

            # Extract dates from json
            waste_type = "Rubbish"
            if "nextRubbishDateSubText" in rubbish_data["result"]:
                if not rubbish_data["result"]["nextRubbishDateSubText"]:
                    dt_str = (
                        rubbish_data["result"]["nextRubbishDateText"]
                        + " "
                        + str(date.today().year)
                    )
                else:
                    if len(rubbish_data["result"]["nextRubbishDateText"]) < 12:
                        dt_str = (
                            rubbish_data["result"]["nextRubbishDateSubText"]
                            + " "
                            + str(date.today().year)
                        )
                dt_zulu = datetime.strptime(dt_str, "%A %d %B %Y")
                dt_local = dt_zulu.astimezone(None)
                entries.append(
                    Collection(
                        date=fix_date(dt_local.date()),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

            waste_type = "Recycling"
            if "nextRecyclingDateSubText" in recycling_data["result"]:
                if not recycling_data["result"]["nextRecyclingDateSubText"]:
                    dt_str = (
                        recycling_data["result"]["nextRecyclingDateText"]
                        + " "
                        + str(date.today().year)
                    )
                else:
                    if len(recycling_data["result"]["nextRecyclingDateText"]) < 12:
                        dt_str = (
                            recycling_data["result"]["nextRecyclingDateSubText"]
                            + " "
                            + str(date.today().year)
                        )
                dt_zulu = datetime.strptime(dt_str, "%A %d %B %Y")
                dt_local = dt_zulu.astimezone(None)
                entries.append(
                    Collection(
                        date=fix_date(dt_local.date()),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries
