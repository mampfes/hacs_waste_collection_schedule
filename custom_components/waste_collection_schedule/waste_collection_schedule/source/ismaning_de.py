import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Gemeinde Ismaning – Abfallkalender"
DESCRIPTION = (
    "Source for the waste collection schedule of the community Ismaning, Germany."
)
URL = "https://ismaning.de/umwelt-energie/abfall/abfallkalender/"
COUNTRY = "de"

SOURCE_CODEOWNERS = ["@Kufi089"]

AJAX_URL = "https://ismaning.de/wp-admin/admin-ajax.php"
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://ismaning.de/umwelt-energie/abfall/abfallkalender/",
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.BIO_KITCHEN,
    "Papiertonne": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Giftmobil": Icons.HAZARDOUS,
    "Giftmobil-Samstag": Icons.HAZARDOUS,
    "Giftmobil-Fischerhäuser": Icons.HAZARDOUS,
    "Christbaumabholung": Icons.CHRISTMAS_TREE,
    "Rama-Dama": Icons.BULKY,
}

TEST_CASES = {
    "Am Englischen Garten (ohne Hausnummer)": {"street": "Am Englischen Garten"},
    "Bahnhofstraße 5 (mit Hausnummer)": {"street": "Bahnhofstraße", "street_nr": "5"},
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "street_nr": "Hausnummer",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "de": (
        "Geben Sie Ihre Straße ein. Wenn die Straße eine Hausnummer benötigt, wird "
        "diese im nächsten Schritt als Auswahl abgefragt."
    ),
}


class Source:
    def __init__(self, street: str = "", street_nr: str = "") -> None:
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._ics = ICS()
        self._year = datetime.now(ZoneInfo("Europe/Berlin")).year

        self._street = self._resolve_street(street)
        street_type = self._ajax(
            action="iap_get_first_at_frontend", street=self._street, year=self._year
        ).strip()

        self._street_nr: str | None = None
        if street_type == "2":
            gebiet = self._street_gebietsnummer
            numbers = self._house_numbers(self._street, gebiet)
            street_nr = street_nr.strip()
            if not street_nr:
                raise SourceArgumentRequiredWithSuggestions(
                    "street_nr",
                    "Diese Straße benötigt eine Hausnummer.",
                    numbers,
                )
            if street_nr not in numbers:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_nr", street_nr, numbers
                )
            self._street_nr = street_nr
        # street_type == "1": no house number needed (street_nr is ignored).

    def fetch(self) -> list[Collection]:
        params = {"street": self._street, "year": self._year}
        if self._street_nr is not None:
            params["hnr"] = self._street_nr

        ics_url = self._ajax(action="ics_non_notification_generation", **params).strip()
        if not ics_url.startswith("http"):
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "Der Server konnte für diese Auswahl keinen Abfahrtskalender "
                "erstellen.",
            )

        response = self._session.get(ics_url, timeout=30)
        response.raise_for_status()
        # Ismaning does not send a charset header; requests defaults to
        # ISO-8859-1 which mangles the German summaries. The ICS is UTF-8.
        dates = self._ics.convert(response.content.decode("utf-8"))

        return [
            Collection(date, waste_type.strip(), icon=ICON_MAP.get(waste_type.strip()))
            for date, waste_type in dates
        ]

    def _ajax(self, **params) -> str:
        response = self._session.post(AJAX_URL, data=params, timeout=30)
        response.raise_for_status()
        return response.text

    def _resolve_street(self, street: str) -> str:
        street = street.strip()
        streets = self._streets()
        if not streets:
            raise SourceArgumentNotFound(
                "street", street, "Es wurden keine Straßen gefunden."
            )
        if not street:
            raise SourceArgumentRequiredWithSuggestions(
                "street", "Bitte wählen Sie Ihre Straße.", [n for _, n in streets]
            )

        target = street.casefold()
        for gebiet, name in streets:
            if name.strip().casefold() == target:
                self._street_gebietsnummer = gebiet
                return name.strip()

        raise SourceArgumentNotFoundWithSuggestions(
            "street", street, [n.strip() for _, n in streets]
        )

    def _streets(self) -> list[tuple[str, str]]:
        html = self._ajax(action="get_streets", year=self._year)
        return re.findall(r'<option data-gebietsnummer="(\d+)">([^<]+)</option>', html)

    def _house_numbers(self, street: str, gebiet: str) -> list[str]:
        html = self._ajax(
            action="iap_get_erg_by_second",
            street=street,
            year=self._year,
            gebietsnummer=gebiet,
        )
        options = re.findall(r"<option[^>]*>([^<]+)</option>", html)
        return [o.strip() for o in options if o.strip() and o.strip() != "Bitte wählen"]
