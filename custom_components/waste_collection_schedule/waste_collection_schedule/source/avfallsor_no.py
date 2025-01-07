import datetime
import logging

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Avfall Sør, Kristiansand"
DESCRIPTION = "Source for Avfall Sør, Kristiansand."
URL = "https://avfallsor.no/"
TEST_CASES = {"Auglandslia 1, Kristiansand": {"address": "Auglandslia 1, Kristiansand"}}
_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Bioavfall": "mdi:leaf",
    "Papp og papir": "mdi:package-variant",
    "Plastemballasje": "mdi:recycle",
    "Glass- og metallemballasje": "mdi:bottle-soda",
}


API_URL = "https://avfallsor.no/wp-json/addresses/v1/address"


NO_WEEKDAYS = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]
NO_MONTHS = [
    "januar",
    "februar",
    "mars",
    "april",
    "mai",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "desember",
]


def parse_date(date_str: str) -> datetime.date:
    date_str = date_str.lower()
    for weekday in NO_WEEKDAYS:
        date_str = date_str.replace(weekday, "")

    month_number = None
    for i, month in enumerate(NO_MONTHS):
        if month in date_str:
            month_number = i + 1
            date_str = date_str.replace(month, "")
            break
    if month_number is None:
        raise ValueError("Could not find month in date string %s" % date_str)

    date_str = date_str.replace(".", "").strip()
    try:
        day = int(date_str)
    except ValueError:
        raise ValueError("Day is not an integer: %s" % date_str)

    date_ = datetime.date(datetime.datetime.now().year, month_number, day)
    if datetime.date.today() > date_:
        return date_.replace(year=datetime.datetime.now().year + 1)

    return date_


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self) -> list[Collection]:
        args = {"address": self._address.split(",")[0].strip()}

        r = requests.get(API_URL, params=args)
        r.raise_for_status()
        matches = r.json()
        href: str | None = None

        for match in matches:
            if (
                match["label"]
                .lower()
                .replace(" ", "")
                .replace(",", "")
                .replace(".", "")
                .casefold()
                == self._address.lower()
                .replace(" ", "")
                .replace(",", "")
                .replace(".", "")
                .casefold()
            ):
                href = match["href"]
                break

        if not href:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [match["label"] for match in matches],
            )
        r = requests.get(href)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        pickup_div = (
            soup.select_one("div.pickup-days-large")
            or soup.select_one("div.pickup-days-small")
            or soup.select_one("div.pickup-days")
        )
        if not pickup_div:
            raise ValueError("Could not find pickup days")

        entries = []
        for h3 in soup.select("h3"):
            date_ = parse_date(h3.text)
            div = h3.find_next_sibling("div")

            if not div or not isinstance(div, Tag):
                _LOGGER.warning("Could not find div for %s", h3.text)
                continue

            for text_div in div.select("div.info-boxes-box-info"):
                for span in text_div.select("span"):
                    span.decompose()
                bin_type = text_div.text.strip()

                icon = ICON_MAP.get(bin_type)  # Collection icon
                entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
