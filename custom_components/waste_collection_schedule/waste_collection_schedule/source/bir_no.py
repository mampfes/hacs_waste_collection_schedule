import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "BIR (Bergensområdets Interkommunale Renovasjonsselskap)"
DESCRIPTION = "Askøy, Bergen, Bjørnafjorden, Eidfjord, Kvam, Osterøy, Samnanger, Ulvik, Vaksdal, Øygarden og Voss Kommune (Norway)."
URL = "https://bir.no"

TEST_CASES = {
    "Villa Paradiso": {
        "street_name": "Nordåsgrenda",
        "house_number": 7,
        "house_letter": "",
    },
    "Mardalsrenen 12 B": {
        "street_name": "Mardalsrenen",
        "house_number": "11",
    },
    "Alf Bondes Veg 13 B": {
        "street_name": "Alf Bondes Veg",
        "house_number": "13",
        "house_letter": "B",
    },
    "Alf Bondes Veg 13 A": {
        "street_name": "Alf Bondes Veg",
        "house_number": "13",
        "house_letter": "A",
    },
    "Alf Bondes Veg 13B (combined house_number)": {
        "street_name": "Alf Bondes Veg",
        "house_number": "13B",
    },
}

API_URL = "https://bir.no/api/search/AddressSearch"
ICON_MAP = {
    "restavfall": Icons.GENERAL_WASTE,
    "papir": Icons.PAPER,
    "matavfall": Icons.BIO_KITCHEN,
}


def normalize(text):
    return "".join(str(text).split()).lower()


def strip_street(title, street):
    # Reduce a provider address title to its house-number portion (letter
    # included), so a suggestion can be resubmitted directly as house_number.
    if title.lower().startswith(street.lower()):
        return title[len(street) :].strip()
    return title


def map_icon(text):
    for key, value in ICON_MAP.items():
        if key in text:
            return value
    return "mdi:trash-can"


class Source:
    def __init__(self, street_name, house_number, house_letter=""):
        self._street_name = street_name
        self._house_number = house_number
        self._house_letter = house_letter

    def _search(self, query, headers):
        # The space at the end is serving as a termination character for the query
        return requests.get(
            API_URL, params={"q": f"{query} ", "s": False}, headers=headers
        ).json()

    def _address_id(self, headers):
        street = str(self._street_name).strip()
        number = str(self._house_number).strip()
        letter = str(self._house_letter).strip()

        # Accept the house letter as part of the house number ("13A")
        match = re.fullmatch(r"(\d+)\s*([A-Za-zÆØÅæøå]*)", number)
        if match and not letter:
            number, letter = match.group(1), match.group(2)

        # BIR is inconsistent about the separator: some addresses are indexed
        # as "Alf Bondes Veg 13 A" and others as "Alf Bondes Veg 13B", try both
        queries = (
            [f"{street} {number} {letter}", f"{street} {number}{letter}"]
            if letter
            else [f"{street} {number}"]
        )

        wanted = normalize(f"{street}{number}{letter}")
        results = {}
        for query in queries:
            for result in self._search(query, headers):
                if normalize(result["Title"]) == wanted:
                    return result["Id"]
                results[result["Id"]] = result["Title"]

        # A single hit for a query that contained the whole address is good
        # enough, BIR groups some addresses under a range ("9 A-N")
        if len(results) == 1:
            return next(iter(results))

        if results:
            # Suggestions must be valid house_number values (letter included),
            # not full titles, or picking one would overwrite house_letter
            # with an entire address instead of resolving it (#7523).
            suggestions = sorted(
                strip_street(title, street) for title in results.values()
            )
            raise SourceArgAmbiguousWithSuggestions("house_number", number, suggestions)

        suggestions = sorted(
            strip_street(title, street)
            for title in {r["Title"] for r in self._search(street, headers)}
        )
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number" if suggestions else "street_name",
            number if suggestions else street,
            suggestions[:25],
        )

    def fetch(self):
        headers = {"user-agent": "Home-Assitant-waste-col-sched/0.1"}

        r = requests.get(
            f"{URL}/adressesoek/toemmekalender",
            params={"rId": self._address_id(headers)},
            headers=headers,
        )
        doc = BeautifulSoup(r.content, "html.parser")
        month_containers = doc.select(
            ".main-content .address-page-box .month-container"
        )

        return [
            Collection(
                date=datetime.datetime.strptime(
                    f"{date.text.replace('des', 'dec').replace('mai', 'may').replace('okt', 'oct')} {container.select('.month-title')[0].text.strip().split(' ')[1]}",
                    "%d. %b %Y",
                ).date(),
                t=doc.select(
                    f'.trash-categories > .trash-row > img[src="{category_row.select(".icon > img")[0].get("src")}"] + .trash-text'
                )[0].text,
                icon=map_icon(
                    doc.select(
                        f'.trash-categories > .trash-row > img[src="{category_row.select(".icon > img")[0].get("src")}"] + .trash-text'
                    )[0].text.lower()
                ),
            )
            for container in month_containers
            for category_row in container.select(".category-row")
            for date in category_row.select(".date-item > .date-item-date")
        ]
