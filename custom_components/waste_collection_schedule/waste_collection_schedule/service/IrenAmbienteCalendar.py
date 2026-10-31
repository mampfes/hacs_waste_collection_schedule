"""IrenAmbienteCalendar retrieval and parsing through the shared, verified HTTP session."""

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, TypedDict

from dateutil.rrule import rrulestr

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)
DTSTART_REGEX = re.compile("DTSTART=\\d*T\\d*Z?;?")

# "Settimana pari/dispari come previsto dalla numerazione del calendario annuale"
DISPARI_REGEX = re.compile(r"\bdispari\b", re.IGNORECASE)
PARI_REGEX = re.compile(r"\bpari\b", re.IGNORECASE)

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
    IdFrequenza: str
    FlagFreq: str
    FestivitaCalendario: list[Holiday]
    NonVisibile: bool


class _CalendarClient:
    _session: Any

    def __init__(self, city: str, street: str, house_number: str | int):
        self._city: str = city
        self._street: str = street
        self._house_number: str | int = house_number
        self._address_id: str | None = None

    def get_cities(self, search: str) -> list[CityResultEntry]:
        params = {"api": "comuni", "search": search.lower()}
        r = self._session.get(API_URL, params=params)
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

    def get_streets(self, city_id: str, search: str) -> list[StreetResultEntry]:
        params: dict[str, str | int] = {
            "api": "vie",
            "istat": city_id,
            "search": search.lower(),
        }
        if search == "":
            params["limit"] = 1000
        r = self._session.get(API_URL, params=params)
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

    def get_house_numbers(
        self, city_id: str, street_code: str, search: str
    ) -> list[HnrRestultEntry]:
        params = {
            "api": "civici",
            "istat": city_id,
            "streetcode": street_code,
            "search": search.lower().split("/")[0].split()[0],
        }
        r = self._session.get(API_URL, params=params)
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
            if holiday["DataFestivita"]:
                festivity = datetime.strptime(
                    holiday["DataFestivita"], "%Y-%m-%d"
                ).date()
                if holiday["DataConferimento"]:
                    holiday_map[festivity] = datetime.strptime(
                        holiday["DataConferimento"], "%Y-%m-%d"
                    ).date()
                else:
                    holiday_map[festivity] = festivity
        return holiday_map

    def get_collection_result(self, address_id: str) -> list[CollectionItem]:
        r = self._session.get(COLLECTION_ULR.format(address_id=address_id))
        r.raise_for_status()
        return r

    @staticmethod
    def _fortnightly_parity(item: CollectionItem) -> int:
        """Return the ISO week parity (1 = odd, 0 = even) of a fortnightly (2S) schedule.

        Iren aligns odd/even weeks to the ISO week numbers of the year and states
        which one in the notes ("Settimana pari/dispari come previsto dalla
        numerazione del calendario annuale"). FlagFreq is "N" for both pari and
        dispari zones, so it is only used as a last resort.
        """
        notes = f"{item.get('NotaGenerica') or ''} {item.get('NoteServizio') or ''}"
        # check "dispari" first: it contains "pari"
        if DISPARI_REGEX.search(notes):
            return 1
        if PARI_REGEX.search(notes):
            return 0
        start = item.get("DataInizioValidita")
        if isinstance(start, str) and start:
            try:
                return datetime.fromisoformat(start).isocalendar()[1] % 2
            except ValueError:
                pass
        return 0 if item.get("FlagFreq") == "P" else 1

    def _get_collections(self, response) -> list[dict]:
        data: list[CollectionItem] = response.json()
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
                or (not rulestr.removeprefix("RRULE:").strip())
                or (not rulestr.removeprefix("RDATE:").strip())
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
            # IdFrequenza="2S" is every other week, on odd or even ISO weeks,
            # though the API returns FREQ=WEEKLY. Keep the weekly rule and
            # filter by the ISO week number of each date: a fixed INTERVAL=2
            # drifts after a 53-week year.
            week_parity = None
            if (
                item.get("IdFrequenza") == "2S"
                and "INTERVAL" not in rulestr
                and rulestr.startswith("RRULE:")
            ):
                week_parity = self._fortnightly_parity(item)
                if start_datetime is None:
                    start_datetime = datetime.now() - timedelta(days=10)
            # The API also publishes semicolon-separated ISO dates.
            if rulestr.startswith("RDATE:"):
                dates = rulestr.removeprefix("RDATE:").replace(";", ",").split(",")
                rulestr = "RDATE:" + ",".join(
                    datetime.fromisoformat(value.strip()).strftime("%Y%m%dT%H%M%S")
                    for value in dates
                    if value.strip()
                )
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
                if (
                    week_parity is not None
                    and date_time.isocalendar()[1] % 2 != week_parity
                ):
                    continue
                date_ = date_time.date()
                days_moved = {date_}
                end = False
                while date_ in holidays:
                    date_ = holidays[date_]
                    if date_ in days_moved:
                        end = True
                        break
                    days_moved.add(date_)
                if end or (date_, bin_type) in already_added:
                    continue
                already_added.add((date_, bin_type))
                entries.append({"date": date_, "type": bin_type})
        return entries

    def retrieve(self):
        city_id = self._search_city()
        street_code = self._search_street(city_id)
        address_id = self.search_house_number(city_id, street_code)
        return self.get_collection_result(address_id)

    def parse(self, response):
        return self._get_collections(response)


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
