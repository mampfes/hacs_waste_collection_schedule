from datetime import date

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "1Coast - Central Coast"
DESCRIPTION = "Source for 1Coast - Central Coast."
URL = "https://1coast.com.au/"
TEST_CASES = {
    # "12 MAITLAND ST, NORAH HEAD. CENTRAL COAST 2263": {
    #     "address": "12 MAITLAND ST, NORAH HEAD. CENTRAL COAST 2263"
    # },
    "12 GERMAINE AVE BATEAU BAY CENTRAL COAST 2261": {
        "address": "12 GERMAINE AVE BATEAU BAY CENTRAL COAST 2261"
    },
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


SEARCH_URL = "https://1coast.com.au/ajax.php"
COLLECTION_URL = (
    "https://1coast.com.au/bin-collection/bin-collection-day-address-details"
)


class Source:
    def __init__(self, address: str):
        self._address: str = address

        self._address_id: str | None = None
        self._address_formatted: str | None = None
        self._collectio_params: dict[str, str] | None = None

        self._ics = ICS()

    def _set_address_id(self) -> None:
        r = requests.get(SEARCH_URL, params={"a": "search", "s": self._address})
        r.raise_for_status()
        data = r.json()
        if len(data) == 0:
            raise SourceArgumentNotFound("address", self._address)
        if len(data) == 1:
            return data[0]["id"]

        address_names = []
        for addr in data:
            addr_name = " ".join(addr["name"])
            address_names.append(addr_name)
            if addr_name.lower().replace(" ", "").replace(",", "").replace(
                ".", ""
            ) == self._address.lower().replace(" ", "").replace(",", "").replace(
                ".", ""
            ):
                self._address_id = addr["id"]
                self._address_formatted = ",".join(addr["name"])
                self._collectio_params = addr["collection"]
                return

        raise SourceArgAmbiguousWithSuggestions("address", self._address, address_names)

    def fetch(self) -> list[Collection]:
        fresh_id = False
        if self._address_id is None:
            self._set_address_id()

        try:
            return self._get_collections()
        except Exception as e:
            if fresh_id:
                raise e
            self._set_address_id()
            return self._get_collections()

    def _get_collections(self) -> list[Collection]:
        assert self._address_id is not None
        assert self._address_formatted is not None
        assert self._collectio_params is not None

        args = {
            "a": "unauth-address-search",
            "address": self._address_id,
            self._address_formatted: "",
            "collection[frequency]": self._collectio_params["frequency"],
            "collection[day]": self._collectio_params["day"],
        }

        # get json file
        r = requests.get(COLLECTION_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        # print(soup.prettify())

        def chekc_tag(tag):
            return (
                isinstance(tag, Tag)
                and tag.name == "a"
                and tag.attrs.get("href")
                and tag.attrs["href"].endswith("ics")
            )

        ics_url = (
            soup.find(
                chekc_tag,
            )
            or {}
        ).get("href")
        if not ics_url:
            raise Exception("Could not find ICS URL")

        r = requests.get(ics_url)
        r.raise_for_status()
        collections = []
        if r.text.count("BEGIN:VCALENDAR") == 1:
            collections = self._ics.convert(r.text)
        else:
            for calendar in r.text.split("BEGIN:VCALENDAR")[1:]:
                collections += self._ics.convert("BEGIN:VCALENDAR" + calendar)

        entries = []
        added: set[tuple[date, str]] = set()
        for date_, bin in collections:
            if (date_, bin) in added:
                continue
            added.add((date_, bin))
            icon = ICON_MAP.get(bin.lower())
            entries.append(Collection(date=date_, t=bin, icon=icon))

        return entries


# https://1coast.com.au/bin-collection/bin-collection-day-address-details/?a=unauth-address-search&address=711491&12,GERMAINE%20AVE,BATEAU%20BAY,CENTRAL%20COAST,2261=&collection%5Bfrequency%5D=W21&collection%5Bday%5D=FRI
# https://1coast.com.au/bin-collection/bin-collection-day-address-details/?a=unauth-address-search&address=711491&12,GERMAINE%20AVE,BATEAU%20BAY,CENTRAL%20COAST,2261&collection[frequency]=W21&collection[day]=FRI
