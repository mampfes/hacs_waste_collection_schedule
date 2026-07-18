"""RegioEntsorgung Städteregion Aachen (regioentsorgung.de).

Demonstrates: an Athos "WasteManagementServlet" wizard that, unlike every
other Athos deployment in this codebase (see AthosWasteManagementRetriever),
does not accept known-good field values directly -- each step's own response
carries a fresh ``<select>`` of the options valid *given the previous
choices* (city -> its streets -> that street's house numbers), and the value
actually submitted must be one of those scraped options (matched
case/whitespace-insensitively, with suggestions on a miss). The shared
retriever has no hook for "validate this step's field against the previous
step's own response before submitting it", so this is expressed as a
source-defined retrieve() that re-scrapes each step in turn. Runs the whole
wizard twice near year-end (this year, then a best-effort next year), like
the legacy source did.
"""

from datetime import datetime
from html.parser import HTMLParser
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://tonnen.regioentsorgung.de/WasteManagementRegioentsorgung/WasteManagementServlet"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
_APP = "com.athos.kd.regioentsorgung"


class _FormStateParser(HTMLParser):
    """Scrape every ``<select><option>`` pair keyed by the select's ``name``."""

    def __init__(self):
        super().__init__()
        self.select_options: dict[str, list[tuple[str, str]]] = {}
        self._current_select: str | None = None
        self._current_option_value: str | None = None
        self._current_option_text: list[str] = []

    def _finalize_option(self):
        if self._current_select is None or self._current_option_value is None:
            return
        text = " ".join(part.strip() for part in self._current_option_text).strip()
        self.select_options[self._current_select].append(
            (self._current_option_value or "", text)
        )
        self._current_option_value = None
        self._current_option_text = []

    def finalize(self):
        self._finalize_option()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "select" and "name" in attributes:
            name = attributes["name"]
            if name is None:
                return
            self._finalize_option()
            self._current_select = name
            self.select_options.setdefault(self._current_select, [])
        elif tag == "option" and self._current_select is not None:
            self._finalize_option()
            self._current_option_value = attributes.get("value", "")
            self._current_option_text = []

    def handle_data(self, data):
        if self._current_option_value is not None:
            self._current_option_text.append(data)

    def handle_endtag(self, tag):
        if tag == "option":
            self._finalize_option()
        elif tag == "select":
            self._finalize_option()
            self._current_select = None

    def get_options(self, field_name: str) -> list[str]:
        return [
            text or value
            for value, text in self.select_options.get(field_name, [])
            if (text or value)
        ]


def _parse_form_state(content: str) -> _FormStateParser:
    parser = _FormStateParser()
    parser.feed(content)
    parser.finalize()
    parser.close()
    return parser


def _normalize(value: object) -> str:
    return " ".join(str(value).split()).casefold()


def _resolve_option(field_name: str, value: str, options: list[str]) -> str:
    if value in options:
        return value
    normalized_options = {_normalize(option): option for option in options}
    normalized_value = _normalize(value)
    if normalized_value in normalized_options:
        return normalized_options[normalized_value]
    if options:
        raise SourceArgumentNotFoundWithSuggestions(field_name, value, options)
    raise SourceArgumentNotFound(
        field_name, value, "please check the other address arguments and try again."
    )


@final
class Source(BaseSource):
    TITLE = "RegioEntsorgung Städteregion Aachen"
    DESCRIPTION = "RegioEntsorgung Städteregion Aachen"
    URL = "https://regioentsorgung.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Merzbrück": {"city": "Würselen", "street": "Merzbrück", "house_number": 200},
        "Krefelder Straße": {
            "city": "Würselen",
            "street": "Krefelder Straße",
            "house_number": 10,
        },
    }

    PARAMS = (
        municipality(field="city"),
        street(field="street"),
        house_number(field="house_number"),
    )

    def retrieve(self, source):
        session = source.session
        city = source.params["city"]
        street_name = source.params["street"]
        house_no = str(source.params["house_number"])
        year = datetime.now().year

        responses = [self._get_collection(session, city, street_name, house_no, year)]
        if datetime.now().month == 12:
            try:
                responses.append(
                    self._get_collection(session, city, street_name, house_no, year + 1)
                )
            except Exception:
                pass
        return responses

    @staticmethod
    def _get_collection(
        session, city_in: str, street_in: str, house_no_in: str, year: int
    ):
        r = session.get(
            _API_URL, headers=_HEADERS, params={"SubmitAction": "wasteDisposalServices"}
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        form_state = _parse_form_state(r.text)
        city = _resolve_option("city", city_in, form_state.get_options("Ort"))

        r = session.post(
            _API_URL,
            headers=_HEADERS,
            data={
                "ApplicationName": f"{_APP}.CheckAbfuhrtermineModel",
                "SubmitAction": "CITYCHANGED",
                "Ort": city,
                "Strasse": "",
                "Hausnummer": "",
            },
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        form_state = _parse_form_state(r.text)
        street_name = _resolve_option(
            "street", street_in, form_state.get_options("Strasse")
        )

        r = session.post(
            _API_URL,
            headers=_HEADERS,
            data={
                "ApplicationName": f"{_APP}.CheckAbfuhrtermineModel",
                "SubmitAction": "STREETCHANGED",
                "Ort": city,
                "Strasse": street_name,
                "Hausnummer": "",
            },
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        form_state = _parse_form_state(r.text)
        house_no = _resolve_option(
            "house_number", house_no_in, form_state.get_options("Hausnummer")
        )

        r = session.post(
            _API_URL,
            headers=_HEADERS,
            data={
                "ApplicationName": f"{_APP}.CheckAbfuhrtermineModel",
                "SubmitAction": "forward",
                "Ort": city,
                "Strasse": street_name,
                "Hausnummer": house_no,
                "Zeitraum": f"Jahresübersicht {year}",
            },
        )
        r.raise_for_status()

        r = session.post(
            _API_URL,
            headers=_HEADERS,
            data={
                "ApplicationName": f"{_APP}.AbfuhrTerminModel",
                "SubmitAction": "forward",
            },
        )
        r.raise_for_status()

        r = session.post(
            _API_URL,
            headers=_HEADERS,
            data={
                "ApplicationName": f"{_APP}.AbfuhrTerminDownloadModel",
                **{f"ContainerGewaehlt_{i}": "on" for i in range(1, 10)},
                "ICalErinnerung": "keine Erinnerung",
                "ICalZeit": "06:00 Uhr",
                "SubmitAction": "filedownload_ICAL",
            },
        )
        r.raise_for_status()
        return r

    def parse(self, raw, source=None):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries

    transform = ICSTransformer()

    def __init__(self, city: str, street: str, house_number: "str | int"):
        super().__init__(city=city, street=street, house_number=str(house_number))
