import logging
from datetime import datetime
from typing import Literal
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Afvalstoffendienst.nl"
DESCRIPTION = (
    "Source for 's Hertogenbosch, Heusden, Vught, Oisterwijk, Altena, Bernheze"
)
URL = "https://www.afvalstoffendienst.nl/"


TEST_CASES = {
    "s-hertogenbosch, 5151MS 37 ": {
        "postcode": "5151MS",
        "house_number": 37,
        "region": "s-hertogenbosch",
    },
    "heuden, 5256EJ, 44C": {
        "postcode": "5256EJ",
        "house_number": 44,
        "addition": "C",
        "region": "heusden",
    },
    "vught, 5262 CJ 18": {
        "postcode": "5262 CJ",
        "house_number": "18",
        "region": "vught",
    },
    "Oisterwijk 5062 ER 13": {
        "postcode": "5062 ER",
        "house_number": "13",
        "region": "oisterwijk",
    },
    "Altena 4286 AL 1": {
        "postcode": "4286 AA",
        "house_number": "1",
        "region": "altena",
    },
    "bernheze": {"postcode": "5473 EW", "house_number": 50, "region": "bernheze"},
}

REGIONS = {
    "heusden": {
        "title": "Heusden",
        "url": "https://heusden.afvalstoffendienstkalender.nl/",
        "default_params": {"region": "heusden"},
    },
    "vught": {
        "title": "Vught",
        "url": "https://vught.afvalstoffendienstkalender.nl/",
        "default_params": {"region": "vught"},
    },
    "oisterwijk": {
        "title": "Oisterwijk",
        "url": "https://oisterwijk.afvalstoffendienstkalender.nl/",
        "default_params": {"region": "oisterwijk"},
    },
    "altena": {
        "title": "Altena",
        "url": "https://altena.afvalstoffendienstkalender.nl/",
        "default_params": {"region": "altena"},
    },
    "bernheze": {
        "title": "Bernheze",
        "url": "https://bernheze.afvalstoffendienstkalender.nl/",
        "default_params": {"region": "bernheze"},
    },
    "s-hertogenbosch": {
        "title": "'s-Hertogenbosch",
        "url": "https://www.afvalstoffendienst.nl/",
        "default_params": {"region": "s-hertogenbosch"},
    },
}

EXTRA_INFO = REGIONS.values()

["heusden", "vught", "oisterwijk", "altena", "bernheze", "s-hertogenbosch"]
REGIONS_LITERAL = Literal[
    "heusden", "vught", "oisterwijk", "altena", "bernheze", "s-hertogenbosch"
]

ICON_MAP = {
    "Groente": "mdi:apple",
    "Plastic": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Restafval": "mdi:trash-can",
    "Kerstbomen": "mdi:pine-tree",
}

DUTCH_MONTHS = {
    "januari": "January",
    "februari": "February",
    "maart": "March",
    "april": "April",
    "mei": "May",
    "juni": "June",
    "juli": "July",
    "augustus": "August",
    "september": "September",
    "oktober": "October",
    "november": "November",
    "december": "December",
}

DUTCH_WEEKDAYS = {
    "maandag": "Monday",
    "dinsdag": "Tuesday",
    "woensdag": "Wednesday",
    "donderdag": "Thursday",
    "vrijdag": "Friday",
    "zaterdag": "Saturday",
    "zondag": "Sunday",
}


NORMAL_API_URL = "https://{region}.afvalstoffendienstkalender.nl/nl/{postcode}/{hnr}/"
HERTOGENBOSCH_API_URL = "https://www.afvalstoffendienst.nl/afvalkalender"


class Source:
    def __init__(
        self,
        postcode: str,
        house_number: str | int,
        addition: str | None = None,
        region: REGIONS_LITERAL = "s-hertogenbosch",
    ):
        self._postcode: str = postcode.replace(" ", "").upper()
        self._house_number: str | int = house_number
        self._addition: str | None = addition.lower() if addition else None

        if region.lower() not in REGIONS:
            raise ValueError(f"Invalid region: {region}, must be one of {REGIONS}")

        self._url = NORMAL_API_URL.format(
            postcode=self._postcode, hnr=self._house_number, region=region
        )

        if self._addition:
            self._url += f"{self._addition}/"

        self._cookies = {}
        self._prepare_urls = []
        if region == "s-hertogenbosch":
            self._url = HERTOGENBOSCH_API_URL
            self._cookies = {
                "loginParam": quote(
                    f'{{"username":null,"password":null,"rememberMe":null,"postcode":"{self._postcode}","huisnummer":"{self._house_number}","toevoeging":"{self._addition if self._addition else ""}","debtornumber":""}}'
                )
            }
            self._prepare_urls = [
                "https://www.afvalstoffendienst.nl/bewoners/s-hertogenbosch"
            ]

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        cookies = self._cookies.copy()
        for url in self._prepare_urls:
            s.get(url)
            cookies.update(s.cookies.get_dict())

        # get json file
        r = requests.get(self._url, cookies=cookies)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.select_one("div#jaaroverzicht") or soup.select_one(
            "div.ophaaldagen"
        )
        table = table or soup

        descr_spans = table.select("span.afvaldescr")

        entries = []
        for descr_span in descr_spans:
            bin_type = descr_span.text.strip()
            date_span = descr_span.find_previous_sibling("span")

            if date_span is None:
                # Get text sibbling not inside any tag (e.g. vrijdag 27 december <br> <span THIS TAG>text</span>)
                date_str = descr_span.parent.text.replace(descr_span.text, "").strip()
            else:
                date_str = date_span.text.lower()
            # replace Dutch months and weekdays with English
            for dutch, english in {**DUTCH_MONTHS, **DUTCH_WEEKDAYS}.items():
                date_str = date_str.replace(dutch, english)
            try:
                date = parse(date_str, dayfirst=True, default=datetime.now()).date()
            except ValueError:
                continue
            icon = ICON_MAP.get(bin_type.split()[0].strip("-,"))  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
