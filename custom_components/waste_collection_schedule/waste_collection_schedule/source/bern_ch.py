import hashlib
import re
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Entsorgung + Recycling Stadt Bern"
DESCRIPTION = "Source for waste collection in the city of Bern, Switzerland."
URL = "https://www.bern.ch/themen/umwelt-natur-und-energie/abfall-und-recycling"
COUNTRY = "ch"
SOURCE_CODEOWNERS = ["@sbaerlocher"]

TEST_CASES = {
    "Bundesplatz 1 (Bundeshaus)": {"strasse": "Bundesplatz", "hnr": 1},
    "Helvetiaplatz 5 (Historisches Museum)": {"strasse": "Helvetiaplatz", "hnr": 5},
    "Waisenhausplatz 30 (Polizeiwache)": {"strasse": "Waisenhausplatz", "hnr": 30},
    "Key only (Bundesplatz 1)": {"key": "DC46354136EE5531B312A864FA2C4604"},
}

API_URL = "https://bernentsorgung.glue.ch/erb/web"
SEARCH_URL = f"{API_URL}/searchAddress"
ICAL_URL = f"{API_URL}/ical"

ICON_MAP = {
    "Hauskehricht": Icons.GENERAL_WASTE,
    "Altpapiersammlung": Icons.PAPER,
    # Keys must match the feed's SUMMARY values verbatim. The feed spells this
    # one without the umlaut ("Gruenabfuhr") even though the website shows
    # "Grünabfuhr". ORGANIC is the right member because Bern collects kitchen
    # and garden organics together.
    "Gruenabfuhr": Icons.ORGANIC,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "de": (
        "Strasse und Hausnummer wie auf "
        "https://bernentsorgung.glue.ch/erb/web/index angeben, z. B. "
        "Strasse 'Bundesplatz' und Hausnummer '1'. Hausnummern mit "
        "Zusatz werden als '3a' angegeben. Alternativ kann der "
        "Schlüssel aus dem iKalender-Link (…/ical?key=…) direkt im Feld "
        "'key' eingetragen werden."
    ),
    "en": (
        "Enter street and house number as shown on "
        "https://bernentsorgung.glue.ch/erb/web/index, e.g. street "
        "'Bundesplatz' and house number '1'. House numbers with a suffix "
        "are written as '3a'. Alternatively, paste the key from the "
        "iCalendar link (…/ical?key=…) directly into the 'key' field."
    ),
}

PARAM_DESCRIPTIONS = {
    "de": {
        "strasse": "Strassenname, z. B. 'Bundesplatz'.",
        "hnr": "Hausnummer, z. B. '1' oder '3a'.",
        "key": "Optional: Schlüssel aus dem iKalender-Link, ersetzt Strasse und Hausnummer.",
    },
    "en": {
        "strasse": "Street name, e.g. 'Bundesplatz'.",
        "hnr": "House number, e.g. '1' or '3a'.",
        "key": "Optional: key from the iCalendar link, replaces street and house number.",
    },
}

PARAM_TRANSLATIONS = {
    "de": {
        "strasse": "Strasse",
        "hnr": "Hausnummer",
        "key": "Schlüssel (optional)",
    },
    "en": {
        "strasse": "Street",
        "hnr": "House number",
        "key": "Key (optional)",
    },
}


class Source:
    def __init__(
        self,
        strasse: str | None = None,
        hnr: str | int | None = None,
        key: str | None = None,
    ):
        self._strasse = strasse.strip() if isinstance(strasse, str) else strasse
        self._hnr = str(hnr).strip() if hnr is not None else None
        self._key = key.strip().upper() if isinstance(key, str) else key
        self._ics = ICS()

        if not self._key and not (self._strasse and self._hnr):
            # Point at the field the user actually left empty.
            missing = "strasse" if not self._strasse else "hnr"
            raise SourceArgumentRequired(
                missing,
                "Provide 'strasse' and 'hnr', or 'key' instead.",
            )

    def _search_key(
        self, strasse: str, hnr: str, session: requests.Session
    ) -> tuple[str, list[str]]:
        """Resolve street + house number to the calendar key via the official
        address search, falling back to the documented MD5 derivation.

        Returns the key plus the house numbers the search reported for the
        street, which fetch() offers as suggestions if the key is rejected.
        """
        try:
            r = session.get(SEARCH_URL, params={"query": strasse}, timeout=30)
            r.raise_for_status()
            addresses = r.json()
        except (requests.RequestException, ValueError):
            addresses = []

        # The endpoint is a typeahead: it matches street name prefixes and can
        # return several streets at once, so keep only the requested street.
        matches = [
            a
            for a in addresses
            if isinstance(a, dict)
            and str(a.get("street", "")).lower() == strasse.lower()
        ]

        for address in matches:
            if str(address.get("number", "")).lower() == hnr.lower() and address.get(
                "key"
            ):
                return str(address["key"]), []

        # The house number is not in the response — but the typeahead caps its
        # result list at 20 entries, so on longer streets that says nothing
        # about whether the address exists. Derive the key instead of giving up
        # here: MD5 of street + number, no separator. fetch() reports the
        # numbers found below only if the service also rejects that key.
        key = hashlib.md5(f"{strasse}{hnr}".encode()).hexdigest().upper()
        return key, sorted({str(a.get("number", "")) for a in matches})

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        # __init__ guarantees either a key or both strasse and hnr.
        suggestions: list[str] = []
        if self._key:
            key = self._key
        else:
            key, suggestions = self._search_key(
                str(self._strasse), str(self._hnr), session
            )

        r = session.get(ICAL_URL, params={"key": key}, timeout=30)
        if r.status_code != 200 or "BEGIN:VCALENDAR" not in r.text:
            # The service answers an unknown key with HTTP 500.
            if self._key:
                raise SourceArgumentNotFound(
                    "key", self._key, "The service does not know this key."
                )
            if suggestions:
                # The street is known, so the house number is the wrong part.
                raise SourceArgumentNotFoundWithSuggestions(
                    "hnr", str(self._hnr), suggestions
                )
            raise SourceArgumentNotFound(
                "strasse",
                f"{self._strasse} {self._hnr}",
                "The service does not know this address.",
            )
        r.encoding = "utf-8"

        # The feed carries empty "EXDATE:" lines, which icalendar reports as a
        # broken property. Dropping them keeps the multi-value EXDATE lines
        # (the public-holiday exclusions) intact.
        ics_data = re.sub(r"^EXDATE:\s*\r?\n", "", r.text, flags=re.MULTILINE)

        # The feed bounds each RRULE with UNTIL=<Dec 31>T230000Z. That instant is
        # 00:00 local time on Jan 1, and because the events are all-day, the
        # recurrence yields one phantom collection on New Year's Day — a date the
        # published calendar does not contain. Drop everything after the UNTIL
        # date carried by this feed (read at runtime, no year is assumed) to
        # remove that artifact. This is not a user-facing time-range filter: the
        # source still returns every collection the provider publishes.
        last_day = self._until_date(ics_data)

        entries = []
        for d, waste_type in self._ics.convert(ics_data):
            if last_day and d > last_day:
                continue
            entries.append(
                Collection(date=d, t=waste_type, icon=ICON_MAP.get(waste_type))
            )

        if not entries:
            # Report the argument the user actually configured, so the Home
            # Assistant UI highlights the right field.
            if self._key:
                raise SourceArgumentNotFound(
                    "key",
                    self._key,
                    "No collections returned for this key.",
                )
            raise SourceArgumentNotFound(
                "strasse",
                f"{self._strasse} {self._hnr}",
                "No collections returned for this address.",
            )

        return entries

    @staticmethod
    def _until_date(ics_data: str) -> date | None:
        """Last calendar day covered by the feed, from the RRULE UNTIL value."""
        matches = re.findall(r"UNTIL=(\d{8})T\d{6}Z", ics_data)
        if not matches:
            return None
        return max(datetime.strptime(m, "%Y%m%d").date() for m in matches)
