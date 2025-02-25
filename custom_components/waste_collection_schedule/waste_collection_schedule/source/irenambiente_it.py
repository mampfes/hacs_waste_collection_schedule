import logging
import re
from datetime import date, datetime, timedelta
from typing import TypedDict

import requests
from dateutil.rrule import rrulestr
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)


TITLE = "Iren Ambiente"
DESCRIPTION = "Source for Iren Ambiente."
URL = "https://servizi.irenambiente.it/"
TEST_CASES = {
    "Torino Corso Quintino Sella 133": {
        "city": "Torino",
        "street": "Corso Quintino Sella",
        "house_number": 133,
    },
    "Fiorenzuola D'arda": {
        "city": "Fiorenzuola D'arda",
        "street": "VIALE ROMA",
        "house_number": "11/13",
    },
    "Rossa": {"city": "Vignolo", "street": "VIA BLANGERA", "house_number": 18},
    "Roccavione": {
        "city": "Roccavione",
        "street": "FRAZIONE BRIGNOLA",
        "house_number": 1,
    },
    "Colorno ARGINE COPERMIO OVEST 74": {
        "city": "Colorno",
        "street": "ARGINE COPERMIO OVEST",
        "house_number": 74,
    },
    "Torino Corso Quintino Sella 11 Scala A": {
        "city": "Torino",
        "street": "Corso Quintino Sella",
        "house_number": "11 Scala A",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Make sure your arguments are exactly spelled as shown in the autocomplete suggestions of the Iren Ambiente website: https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html",
    "it": "Assicurati che i tuoi argomenti siano esattamente come mostrato nei suggerimenti di autocompletamento del sito Iren Ambiente: https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html",
}

# DTSTART=20240301T000000Z
DTSTART_REGEX = re.compile(r"DTSTART=\d*T\d*Z?;?")

ICON_MAP = {
    "Carta": "mdi:package-variant",
    "Cartone": "mdi:package-variant",
    "Rifiuto residuo indifferenziato": "mdi:trash-can",
    "Rifiuti Organici": "mdi:leaf",
    "Imballaggi in plastica": "mdi:recycle",
    "Vetro e lattine": "mdi:bottle-soda",
    "Vetro": "mdi:bottle-soda",
    "Imballaggi in plastica e barattolame": "mdi:recycle",
    "Alluminio": "mdi:recycle",
}


PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "it": {
        "city": "Comune",
        "street": "Via/Piazza/Corso",
        "house_number": "N° Civico",
    },
}

API_URL = "https://servizi.irenambiente.it/bin/iam/api-services"
COLLECTION_ULR = (
    "https://net.irenambiente.it/restv1/api/cms/calendarioraccoltacivico/{address_id}"
)


class CityResultEntry(TypedDict):
    Comune: str
    Istat: str


class StreetResultEntry(TypedDict):
    Street: str
    StreetCode: str
    Istat: str


class HnrRestultEntry(TypedDict):
    Civico: str
    AdrNr: str


class CityResult(TypedDict):
    data: list[CityResultEntry]


class StreetResult(TypedDict):
    data: list[StreetResultEntry]


class HnrResult(TypedDict):
    data: list[HnrRestultEntry]


class Holiday(TypedDict):
    DataFestivita: str
    DataConferimento: str


class CollectionItem(TypedDict):
    Materiale: str
    ICalRRule: str
    FestivitaCalendario: list[Holiday]
    NonVisibile: bool


class Source:
    def __init__(self, city: str, street: str, house_number: str | int):
        self._city: str = city
        self._street: str = street
        self._house_number: str | int = house_number

        self._address_id: str | None = None

    @staticmethod
    def get_cities(search: str) -> list[CityResultEntry]:
        params = {"api": "comuni", "search": search.lower()}
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        result_data: CityResult = r.json()
        return result_data["data"]

    def _search_city(self) -> str:
        data = self.get_cities(self._city)
        if not data:
            raise SourceArgumentNotFound("city", self._city)

        for city in data:
            if city["Comune"].lower().replace(" ", "") == self._city.lower().replace(
                " ", ""
            ):
                return city["Istat"]
        raise SourceArgumentNotFoundWithSuggestions(
            "city", self._city, [city["Comune"] for city in data]
        )

    @staticmethod
    def get_streets(city_id: str, search: str) -> list[StreetResultEntry]:
        params: dict[str, str | int] = {
            "api": "vie",
            "istat": city_id,
            "search": search.lower(),
        }
        if search == "":
            params["limit"] = 1000
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        result_data: StreetResult = r.json()

        return result_data["data"]

    def _search_street(self, city_id: str) -> str:
        data = self.get_streets(city_id, self._street)
        if not data:
            data = self.get_streets(city_id, "")

        for street in data:
            if street["Street"].lower().replace(
                " ", ""
            ) == self._street.lower().replace(" ", ""):
                return street["StreetCode"]
        raise SourceArgumentNotFoundWithSuggestions(
            "street", self._street, [street["Street"] for street in data]
        )

    @staticmethod
    def get_house_numbers(
        city_id: str, street_code: str, search: str
    ) -> list[HnrRestultEntry]:
        params = {
            "api": "civici",
            "istat": city_id,
            "streetcode": street_code,
            # only use the first part of the house number if it contains a slash as this seems to break the search and the API should still return the correct address
            "search": search.lower().split("/")[0].split()[0],
        }
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        result_data: HnrResult = r.json()
        return result_data["data"]

    def search_house_number(self, city_id: str, street_code: str) -> str:
        data = self.get_house_numbers(city_id, street_code, str(self._house_number))
        if not data:
            raise SourceArgumentNotFound("house_number", self._house_number)

        for hnr in data:
            if hnr["Civico"].lower().replace(" ", "") == str(
                self._house_number
            ).lower().replace(" ", ""):
                return hnr["AdrNr"]
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", self._house_number, [hnr["Civico"] for hnr in data]
        )

    @staticmethod
    def construct_holiday_map(holidays: list[Holiday]) -> dict[date, date]:
        holiday_map = {}
        for holiday in holidays:
            if holiday["DataFestivita"] and holiday["DataConferimento"]:
                holiday_map[
                    datetime.strptime(holiday["DataFestivita"], "%Y-%m-%d").date()
                ] = datetime.strptime(holiday["DataConferimento"], "%Y-%m-%d").date()
        return holiday_map

    @staticmethod
    def get_collection_result(address_id: str) -> list[CollectionItem]:
        r = requests.get(COLLECTION_ULR.format(address_id=address_id))
        r.raise_for_status()
        return r.json()

    def _get_collections(self) -> list[Collection]:
        if not self._address_id:
            raise ValueError("address id not set")
        data: list[CollectionItem] = self.get_collection_result(self._address_id)

        entries = []
        already_added: set[tuple[date, str]] = set()

        for item in data:
            bin_type = item["Materiale"]
            rulestr = item["ICalRRule"]
            if item["NonVisibile"]:
                continue

            if (
                not rulestr
                or rulestr.lower().startswith("invalid")
                or not rulestr.removeprefix("RRULE:").strip()
                or not rulestr.removeprefix("RDATE:").strip()
            ):
                continue
            start_datetime = None
            if "DTSTART=" in rulestr:
                start_string_match = DTSTART_REGEX.search(rulestr)
                if start_string_match:
                    start_string = start_string_match.group(0)
                    start_datetime = datetime.strptime(
                        start_string.replace("DTSTART=", "").strip(";"),
                        "%Y%m%dT%H%M%SZ",
                    )
                rulestr = DTSTART_REGEX.sub("", rulestr).strip(";")

            try:
                if start_datetime:
                    rule = rrulestr(rulestr, dtstart=start_datetime)
                else:
                    rule = rrulestr(rulestr)
            except Exception as e:
                _LOGGER.warning(
                    f"ERROR: {e}, could not parse collection rule: {rulestr}, for {bin_type}"
                )
                continue

            holidays = self.construct_holiday_map(item["FestivitaCalendario"])

            for date_time in rule.between(
                datetime.now() - timedelta(days=10),
                datetime.now() + timedelta(days=365),
            ):
                date_ = date_time.date()
                days_moved = {date_}
                end = False
                while date_ in holidays:
                    # Holidays may point to other holidays which may point back to the original date (the day should be completely skipped)
                    date_ = holidays[date_]
                    if date_ in days_moved:
                        end = True
                        break
                    days_moved.add(date_)

                if end or (date_, bin_type) in already_added:
                    continue
                already_added.add((date_, bin_type))
                entries.append(
                    Collection(date=date_, t=bin_type, icon=ICON_MAP.get(bin_type))
                )
        return entries

    def fetch(self) -> list[Collection]:
        fresh_data = False
        if not self._address_id:
            city_id = self._search_city()
            street_code = self._search_street(city_id)
            self._address_id = self.search_house_number(city_id, street_code)
            fresh_data = True

        try:
            return self._get_collections()
        except Exception:
            if fresh_data:
                raise

        city_id = self._search_city()
        street_code = self._search_street(city_id)
        self._address_id = self.search_house_number(city_id, street_code)
        return self._get_collections()
