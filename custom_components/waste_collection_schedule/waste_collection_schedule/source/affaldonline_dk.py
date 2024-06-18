import logging
import random
import re
from datetime import date, datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Affaldonline"
DESCRIPTION = "Affaldonline"
URL = "https://affaldonline.dk"
API_URL = "https://www.affaldonline.dk/kalender/{municipality}/showInfo.php"

_LOGGER = logging.getLogger("waste_collection_schedule.affaldonline_dk")

PARSERS = {
    "default": {
        "description": "Næste tømningsdag: DD den D MMMMM YYYY (waste_type_1, waste_type_2)",
        "regex": r"(\d{1,2})\. (\w+) (\d{4})",
        "enabled": True,
    },
    "silkeborg": {
        "description": "A table with dates in the format DD-MM and waste types",
        "regex": r"(\d{2})-(\d{2})",
        "enabled": True,
    },
    "favrskov": {
        "description": "Blåmejsevej 1 (8382 Hinnerup) with multiple waste types",
        "regex": r"Næste tømningsdag: (\w+) den (\d{1,2})\. (\w+) (\d{4})",
        "enabled": True,
    },
    "pdf": {
        "description": "Not yet supported parser for PDF files",
        "regex": None,
        "enabled": False,
    },
}

AFFALDONLINE_MUNICIPALITIES = {
    "aeroe": {
        "title": "Ærø Kommune",
        "url": "https://www.aeroekommune.dk/",
        "parser": "default",
        "values": "Nørregade|1||||5970|Ærøskøbing|1228262|448776|0",
    },
    "assens": {
        "title": "Assens Forsyning",
        "url": "https://www.assensforsyning.dk/",
        "parser": "default",
        "values": "Nørregade|1||||5610|Assens|10894|430000|0",
    },
    "favrskov": {
        "title": "Favrskov Forsyning",
        "url": "https://www.favrskovforsyning.dk",
        "parser": "favrskov",
        "values": "Nørregade|1||||8382|Hinnerup|6443|108156|0",
    },
    "fanoe": {
        "title": "Fanø Kommune",
        "url": "https://fanoe.dk/",
        "parser": "pdf",
        "values": "Nørre Klit|5||||6720|Fanø|2582|1747246|0",
    },
    "fredericia": {
        "title": "Fredericia Kommune Affald & Genbrug",
        "url": "https://affaldgenbrug-fredericia.dk/",
        "parser": "pdf",
        "values": "Nørre Allé|5||||7000|Fredericia|11079971|1907927|0",
    },
    "langeland": {
        "title": "Langeland Forsyning",
        "url": "https://www.langeland-forsyning.dk/",
        "parser": "default",
        "values": "Nørregade|1||||5900|Rudkøbing|3535|383566|0",
    },
    "middelfart": {
        "title": "Middelfart Kommune",
        "url": "https://middelfart.dk/",
        "parser": "default",
        "values": "Nørregade|2||||5592|Ejby|11288085|6496420|0",
    },
    "nyborg": {
        "title": "Nyborg Forsyning & Service A/S",
        "url": "https://www.nfs.as/",
        "parser": "pdf",
        "values": "Nørregade|5||||5800|Nyborg|8896288|552542|0",
    },
    "rebild": {
        "title": "Rebild Kommune",
        "url": "https://rebild.dk/",
        "parser": "default",
        "values": "Nørregade|1||||9500|Hobro|4676913|1012588|0",
    },
    "silkeborg": {
        "title": "Silkeborg Forsyning",
        "url": "https://www.silkeborgforsyning.dk/",
        "parser": "silkeborg",
        "values": "Nørregade|5||||8620|Kjellerup|45814316|1291964|0",
    },
    "soroe": {
        "title": "Sorø Kommune",
        "url": "https://soroe.dk/",
        "parser": "pdf",
        "values": "Nørrevej|4| |||4180|Sorø|8569|8838|0|0",
    },
    "vejle": {
        "title": "Vejle Kommune",
        "url": "https://www.vejle.dk/",
        "parser": "default",
        "values": "Nørregade|69||||7100|Vejle|16285351|16285351|0",
    },
}

EXTRA_INFO = [
    {
        "title": info["title"],
        "url": info["url"],
        "default_params": {"municipality": municipality},
    }
    for municipality, info in AFFALDONLINE_MUNICIPALITIES.items()
]


def select_test_cases(municipalities, mode="random_one_from_each_parser"):
    test_cases = {}
    parser_test_cases = {}

    for name, info in municipalities.items():
        parser = info["parser"]
        if PARSERS[parser]["enabled"]:
            if parser not in parser_test_cases:
                parser_test_cases[parser] = []
            parser_test_cases[parser].append((name, info))

    if mode == "random_one_from_each_parser":
        for parser, cases in parser_test_cases.items():
            selected_case = random.choice(cases)
            test_cases[selected_case[0]] = {
                "municipality": selected_case[0],
                "values": selected_case[1]["values"],
            }
    elif mode == "first_from_each_parser":
        for parser, cases in parser_test_cases.items():
            selected_case = cases[0]
            test_cases[selected_case[0]] = {
                "municipality": selected_case[0],
                "values": selected_case[1]["values"],
            }
    elif mode == "random_one":
        all_cases = [case for cases in parser_test_cases.values() for case in cases]
        selected_case = random.choice(all_cases)
        test_cases[selected_case[0]] = {
            "municipality": selected_case[0],
            "values": selected_case[1]["values"],
        }
    elif mode == "first_one":
        first_parser = list(parser_test_cases.keys())[0]
        selected_case = parser_test_cases[first_parser][0]
        test_cases[selected_case[0]] = {
            "municipality": selected_case[0],
            "values": selected_case[1]["values"],
        }
    elif mode == "all":
        for parser, cases in parser_test_cases.items():
            for case in cases:
                test_cases[case[0]] = {
                    "municipality": case[0],
                    "values": case[1]["values"],
                }

    return test_cases


# Dynamically generate TEST_CASES from the AFFALDONLINE_MUNICIPALITIES dictionary
TEST_CASES = select_test_cases(
    AFFALDONLINE_MUNICIPALITIES, mode="first_from_each_parser"
)

DANISH_MONTHS = [
    "januar",
    "februar",
    "marts",
    "april",
    "maj",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "december",
]


class Source:
    def __init__(self, municipality: str, values: str):
        _LOGGER.debug(
            "Initializing Source with municipality=%s, values=%s", municipality, values
        )
        self._api_url = API_URL.format(municipality=municipality)
        self._values = values
        self._parser_type = AFFALDONLINE_MUNICIPALITIES.get(municipality, {}).get(
            "parser"
        )
        if not self._parser_type:
            raise ValueError(f"Municipality {municipality} is not supported")

        parser = getattr(self, f"_parse_{self._parser_type}", None)
        if parser is None:
            raise ValueError(f"Parser method for {self._parser_type} not implemented")
        if not callable(parser):
            raise ValueError(f"Parser method for {self._parser_type} is not callable")

        self._parser_method = parser

    def fetch(self) -> List[Collection]:
        _LOGGER.debug("Fetching data from %s", self._api_url)

        entries: List[Collection] = []

        post_data = {"values": self._values}

        response = requests.post(self._api_url, data=post_data)
        response.raise_for_status()

        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        entries.extend(self._parser_method(soup))

        return entries

    def _parse_default(self, soup: BeautifulSoup) -> List[Collection]:
        entries: List[Collection] = []

        next_pickup_info = soup.find_all(string=re.compile("Næste tømningsdag:"))
        if not next_pickup_info:
            raise ValueError(
                "No waste schemes found. Please check the provided values."
            )

        for info in next_pickup_info:
            text = info.strip()
            match = re.search(r"(\d{1,2})\. (\w+) (\d{4})", text)
            if match:
                try:
                    day = int(match.group(1))
                    month_name = match.group(2)
                    year = int(match.group(3))
                    month_index = DANISH_MONTHS.index(month_name) + 1
                    formatted_date = date(year, month_index, day)

                    # Extract waste types from the text
                    waste_type_search = re.search(r"\((.*?)\)", text)
                    if waste_type_search is None:
                        _LOGGER.warning("No waste type found in string: %s", text)
                        continue
                    waste_types_text = waste_type_search.group(1)

                    waste_types = [
                        waste_type.strip() for waste_type in waste_types_text.split(",")
                    ]

                    for waste_type in waste_types:
                        entries.append(Collection(date=formatted_date, t=waste_type))
                        _LOGGER.debug(
                            "Added collection: date=%s, type=%s",
                            formatted_date,
                            waste_type,
                        )
                except ValueError as e:
                    _LOGGER.error("Error parsing date: %s from string: %s", e, text)
            else:
                _LOGGER.warning("No valid date found in string: %s", text)

        return entries

    def _parse_silkeborg(self, soup: BeautifulSoup) -> List[Collection]:
        entries: List[Collection] = []

        table = soup.find("table")
        if not table:
            raise ValueError(
                "No waste collection table found. Please check the provided values."
            )

        current_year = datetime.now().year
        current_month = datetime.now().month

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 2:
                # Extract date and waste type
                date_str = cells[0].get_text(strip=True)
                waste_types = cells[1].get_text(strip=True)

                match = re.search(r"(\d{2})-(\d{2})", date_str)
                if match:
                    day = int(match.group(1))
                    month = int(match.group(2))

                    # Determine the year based on the current month
                    collection_year = current_year
                    if month < current_month:
                        collection_year += 1

                    collection_date = date(collection_year, month, day)

                    for waste_type in waste_types.split(","):
                        entries.append(
                            Collection(date=collection_date, t=waste_type.strip())
                        )
                        _LOGGER.debug(
                            "Added collection: date=%s, type=%s",
                            collection_date,
                            waste_type.strip(),
                        )

        return entries

    def _parse_favrskov(self, soup: BeautifulSoup) -> List[Collection]:
        entries: List[Collection] = []

        strong_tags = soup.find_all("strong")
        if not strong_tags:
            raise ValueError(
                "No waste schemes found. Please check the provided values."
            )

        for strong_tag in strong_tags:
            waste_type = strong_tag.get_text(strip=True)
            next_sibling = strong_tag.find_next_sibling(text=True)
            if next_sibling and "Næste tømningsdag" in next_sibling:
                match = re.search(r"(\d{1,2})\. (\w+) (\d{4})", next_sibling)
                if match:
                    try:
                        day = int(match.group(1))
                        month_name = match.group(2)
                        year = int(match.group(3))
                        month_index = DANISH_MONTHS.index(month_name) + 1
                        formatted_date = date(year, month_index, day)

                        entries.append(Collection(date=formatted_date, t=waste_type))
                        _LOGGER.debug(
                            "Added collection: date=%s, type=%s",
                            formatted_date,
                            waste_type,
                        )
                    except ValueError as e:
                        _LOGGER.error(
                            "Error parsing date: %s from string: %s", e, next_sibling
                        )
                else:
                    _LOGGER.warning("No valid date found in string: %s", next_sibling)

        return entries
