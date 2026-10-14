"""HvcCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import logging
from datetime import datetime
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": get_main_url(s["api_url"]),
            "default_params": {"service": extract_service_name(s["api_url"])},
        }
        for s in SERVICE_MAP
    ]


_LOGGER = logging.getLogger(__name__)
SERVICE_MAP = [
    {
        "title": "Alpen an den Rijn",
        "api_url": "https://afvalkalender.alphenaandenrijn.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Cranendonck",
        "api_url": "https://afvalkalender.cranendonck.nl",
        "icons": {},
    },
    {"title": "Cyclus NV", "api_url": "https://cyclusnv.nl", "icons": {}},
    {"title": "Dar", "api_url": "https://afvalkalender.dar.nl", "icons": {}},
    {
        "title": "Den Haag",
        "api_url": "https://huisvuilkalender.denhaag.nl",
        "icons": {},
    },
    {"title": "GAD", "api_url": "https://inzamelkalender.gad.nl", "icons": {}},
    {
        "title": "Gemeente Berkelland",
        "api_url": "https://afvalkalender.gemeenteberkelland.nl",
        "icons": {},
    },
    {
        "title": "HVC Groep",
        "api_url": "https://inzamelkalender.hvcgroep.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Lingewaard",
        "api_url": "https://afvalwijzer.lingewaard.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Middelburg + Vlissingen",
        "api_url": "https://afvalwijzer.middelburgvlissingen.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Peel en Maas",
        "api_url": "https://afvalkalender.peelenmaas.nl",
        "icons": {},
    },
    {"title": "PreZero", "api_url": "https://inzamelwijzer.prezero.nl", "icons": {}},
    {
        "title": "Purmerend",
        "api_url": "https://afvalkalender.purmerend.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Schouwen-Duiveland",
        "api_url": "https://afvalkalender.schouwen-duiveland.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Sliedrecht",
        "api_url": "https://afvalkalender.sliedrecht.nl",
        "icons": {},
    },
    {
        "title": "Spaarnelanden",
        "api_url": "https://afvalwijzer.spaarnelanden.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Sudwest-Fryslan",
        "api_url": "https://afvalkalender.sudwestfryslan.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Venray",
        "api_url": "https://afvalkalender.venray.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Voorschoten",
        "api_url": "https://afvalkalender.voorschoten.nl",
        "icons": {},
    },
    {
        "title": "Gemeente Waalre",
        "api_url": "https://afvalkalender.waalre.nl",
        "icons": {},
    },
    {
        "title": "Mijn Afval Zaken - BUCH",
        "api_url": "https://www.mijnafvalzaken.nl",
        "icons": {},
    },
    {"title": "Reinis", "api_url": "https://reinis.nl", "icons": {}},
    {"title": "RWM", "api_url": "https://rwm.nl", "icons": {}},
    {"title": "ZRD", "api_url": "https://www.zrd.nl", "icons": {}},
]


def extract_service_name(api_url):
    name = api_url.split(".")[-2]
    name = name.split("/")[-1]
    return name


def get_service_name_map():
    return {
        extract_service_name(s["api_url"]): (s["api_url"], s["icons"])
        for s in SERVICE_MAP
    }


def get_main_url(url):
    x = url.split(".")[-2:]
    x[0] = x[0].removeprefix("https://")
    return "https://" + ".".join(x)


class _CalendarClient:
    _session: Any

    def __init__(
        self, postal_code, house_number, house_letter="", suffix="", service="hvcgroep"
    ):
        self.postal_code = postal_code
        self.house_number = house_number
        self.house_letter = house_letter
        self.suffix = suffix
        self._url, self._icons = get_service_name_map()[service]

    def retrieve(self):
        r = self._session.get(
            f"{self._url}/adressen/{self.postal_code}:{self.house_number}"
        )
        r.raise_for_status()
        data = r.json()
        if len(data) == 0:
            raise SourceArgumentNotFound("postal_code", self.postal_code)
        bag_id = data[0]["bagid"]
        if len(data) > 1 and (self.house_letter or self.suffix):
            _LOGGER.info(f"Checking {self.house_letter} {self.suffix}")
            for address in data:
                if (
                    address["huisletter"].lower() == self.house_letter.lower()
                    and address["toevoeging"] == self.suffix
                ):
                    bag_id = address["bagid"]
                    break
        r = self._session.get(f"{self._url}/rest/adressen/{bag_id}/afvalstromen")
        r.raise_for_status()
        waste_flows = r.json()
        r = self._session.get(
            f"{self._url}/rest/adressen/{bag_id}/kalender/{datetime.today().year}"
        )
        r.raise_for_status()
        return r, waste_flows

    def parse(self, raw):
        r, waste_flows = raw
        data = r.json()
        entries = []
        for item in data:
            waste_details = [
                x for x in waste_flows if x["id"] == item["afvalstroom_id"]
            ]
            entries.append(
                {
                    "date": datetime.strptime(item["ophaaldatum"], "%Y-%m-%d").date(),
                    "type": waste_details[0]["title"],
                }
            )
        return entries


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
