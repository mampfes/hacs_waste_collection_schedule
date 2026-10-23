"""MyWasteWatcherCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

BASE_URL = "https://www.mywastewatcher.de/{app_path}/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.mywastewatcher.de/",
}
_FORM = "ctl00$MainContent$frmKalender$"
_FORM_ID = "ctl00_MainContent_frmKalender_"
_DATA_ROW_RE = re.compile('<tr[^>]*class=\\"[^\\"]*dxgvDataRow.*?</tr>', re.DOTALL)
_CELL_RE = re.compile("<td.*?</td>", re.DOTALL)
_CALLBACK_STATE_RE = re.compile("'callbackState':'([^']+)'")
_GRID_STATE_RE = re.compile(
    "ASPxClientGridView,'" + _FORM_ID + "dgvPickUpDates'.*?'callbackState':'([^']+)'",
    re.DOTALL,
)


class _CalendarClient:
    _session: Any

    def __init__(
        self,
        oguid: str = "B3E02353-2090-4EFA-B3C7-AEC81FBC1E6F",
        app_path: str = "abfallkalenderdk",
        ort: str | None = None,
        strasse: str | None = None,
        ortsteil: str | None = None,
        bemerkung: str | None = None,
    ):
        if not strasse:
            raise SourceArgumentRequired(
                "strasse", "the street is needed to select the correct schedule"
            )
        self._oguid = oguid.lower()
        self._app_path = app_path
        self._ort = ort or ""
        self._strasse = strasse
        self._ortsteil = ortsteil or ""
        self._bemerkung = bemerkung or ""
        self._base_url = BASE_URL.format(app_path=app_path)
        self._page_url = f"{self._base_url}default.aspx?oguid={self._oguid}"

    def _parse_response(self, r: requests.Response) -> BeautifulSoup:
        r.raise_for_status()
        r.encoding = "utf-8"
        return BeautifulSoup(r.text, "html.parser")

    def _build_base_form(self, soup: BeautifulSoup) -> dict[str, str]:
        """Build the form payload from the current page state.

        Hidden fields carry the ASP.NET ViewState; text fields carry the
        DevExpress control state (including the visually hidden checkbox
        state inputs, which render as text inputs with value "C"/"U").
        """
        data: dict[str, str] = {}
        for inp in soup.find_all("input"):
            name = inp.get("name") or inp.get("id")
            if not isinstance(name, str) or not name:
                continue
            itype = inp.get("type", "text")
            if itype == "hidden":
                value = inp.get("value") or ""
                if not isinstance(value, str):
                    raise ValueError("Invalid hidden form value")
                data[name] = value
            elif itype == "text":
                val = inp.get("value") or ""
                if not isinstance(val, str):
                    raise ValueError("Invalid text form value")
                if val or "State" in name or "_VI" in name or ("DDD" in name):
                    data[name] = val
        return data

    def _select_city(self, session: requests.Session) -> BeautifulSoup:
        """Load the page and select the city (the oguid is the city VI value)."""
        r = session.get(self._page_url, allow_redirects=True)
        soup = self._parse_response(r)
        data = self._build_base_form(soup)
        data["__EVENTTARGET"] = _FORM + "cboCities"
        data["__EVENTARGUMENT"] = ""
        data[_FORM_ID + "cboCities_VI"] = self._oguid
        data[_FORM + "cboCities"] = self._ort
        data[_FORM + "cboCities$DDD$L"] = self._oguid
        return self._parse_response(session.post(self._page_url, data=data))

    def _find_street_guid(self, soup: BeautifulSoup) -> tuple[str | None, list[str]]:
        """
        Extract the DevExpress GUID for the matching street from the page JS.
        The itemsValue array in the ListBox createControl call maps 1:1 to the
        HTML table rows (Straße, Ortsteil, Bemerkung).
        Returns (guid, all_street_labels) — guid is None when no match found.
        all_street_labels can be used as suggestions in the error message.
        """
        html = str(soup)
        match = re.search(
            "createControl\\(ASPxClientListBox,'"
            + _FORM_ID
            + "cboStreets_DDD_L'.*?'itemsValue':\\[([^\\]]+)\\]",
            html,
            re.DOTALL,
        )
        if not match:
            return (None, [])
        guids = re.findall(
            "'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'",
            match.group(1),
            re.I,
        )
        table = soup.find("table", {"id": _FORM_ID + "cboStreets_DDD_L_LBT"})
        if not table:
            return (None, [])
        rows = table.find_all("tr")
        all_streets: list[str] = []
        for i, row in enumerate(rows):
            if i >= len(guids):
                break
            cells = row.find_all("td")
            if not cells:
                continue
            street = cells[0].get_text(strip=True)
            ortsteil = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            bemerkung = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            label = street
            if ortsteil:
                label += f" ({ortsteil})"
            if bemerkung:
                label += f" – {bemerkung}"
            all_streets.append(label)
            if self._strasse.lower() != street.lower():
                continue
            if self._ortsteil and self._ortsteil.lower() != ortsteil.lower():
                continue
            if self._bemerkung and self._bemerkung.lower() != bemerkung.lower():
                continue
            return (guids[i], all_streets)
        return (None, all_streets)

    def _split_street_label(self) -> bool:
        """Split a combined "Street (Ortsteil) – Bemerkung" suggestion label.

        The config flow re-offers the labels built in _find_street_guid as a
        dropdown when the street was not found; accept a picked label as
        strasse input by splitting it back into its parts.
        Returns True if strasse was changed.
        """
        match = re.fullmatch("(.+?)(?: \\(([^()]+)\\))?(?: – (.+))?", self._strasse)
        if not match or (not match.group(2) and (not match.group(3))):
            return False
        self._strasse = match.group(1)
        self._ortsteil = self._ortsteil or match.group(2) or ""
        self._bemerkung = self._bemerkung or match.group(3) or ""
        return True

    def _collection(
        self, bin_type: str, date_str: str, description: str | None
    ) -> dict | None:
        try:
            day = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            return None
        return {"date": day, "type": bin_type, "description": description}

    def _parse_grid_page(self, soup: BeautifulSoup) -> list[dict]:
        """Parse the dgvPickUpDates grid of a full page into Collection entries."""
        entries: list[dict] = []
        table = soup.find("table", {"id": re.compile("dgvPickUpDates_DXMainTable")})
        if not table:
            return entries
        for row in table.find_all("tr"):
            classes = row.get("class") or ""
            cls = " ".join(classes) if isinstance(classes, list) else classes
            if "dxgvDataRow" not in cls:
                continue
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            entries.extend(self._entries_from_cells(cells))
        return entries

    def _parse_grid_fragment(self, text: str) -> list[dict]:
        """Parse grid rows out of a DevExpress callback response.

        The callback payload wraps the grid HTML in a JavaScript string that
        html.parser cannot digest as a whole, so the data rows are extracted
        with regexes and parsed individually.
        """
        entries: list[dict] = []
        for row_html in _DATA_ROW_RE.findall(text):
            cells = [
                BeautifulSoup(cell, "html.parser").get_text(strip=True)
                for cell in _CELL_RE.findall(row_html)
            ]
            entries.extend(self._entries_from_cells(cells))
        return entries

    def _entries_from_cells(self, cells: list[str]) -> list[dict]:
        if len(cells) < 3:
            return []
        bin_type, date_str = (cells[1], cells[2])
        if not bin_type or not date_str:
            return []
        description = cells[5] if len(cells) > 5 else None
        collection = self._collection(bin_type, date_str, description or None)
        return [collection] if collection else []

    def retrieve(self) -> Any:
        session = self._session
        session.headers.update(_HEADERS)
        soup = self._select_city(session)
        letter = self._strasse[0].upper()
        if letter != "A":
            data = self._build_base_form(soup)
            data["__EVENTTARGET"] = _FORM + "cboBeginntMit"
            data["__EVENTARGUMENT"] = ""
            data[_FORM_ID + "cboBeginntMit_VI"] = letter
            data[_FORM + "cboBeginntMit"] = letter
            soup = self._parse_response(session.post(self._page_url, data=data))
        street_guid, suggestions = self._find_street_guid(soup)
        if not street_guid and self._split_street_label():
            street_guid, suggestions = self._find_street_guid(soup)
        if not street_guid:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", self._strasse, suggestions
            )
        if letter != "A":
            session = self._session
            session.headers.update(_HEADERS)
            soup = self._select_city(session)
        data = self._build_base_form(soup)
        data["__EVENTTARGET"] = _FORM + "cboStreets"
        data["__EVENTARGUMENT"] = ""
        data[_FORM_ID + "cboStreets_VI"] = street_guid
        data[_FORM + "cboStreets"] = self._strasse
        data[_FORM + "cboStreets$DDD$L"] = street_guid
        soup = self._parse_response(session.post(self._page_url, data=data))
        btn = soup.find("input", {"id": _FORM_ID + "btnTermineHolen_I"})
        data = self._build_base_form(soup)
        if btn is not None:
            button_name = btn.get("name")
            button_value = btn.get("value") or "Termine abrufen"
            if not isinstance(button_name, str) or not isinstance(button_value, str):
                raise ValueError("Invalid calendar submit control")
            data[button_name] = button_value
        r = session.post(self._page_url, data=data)
        soup = self._parse_response(r)
        responses = [r]
        page_match = re.search("Seite \\d+ von (\\d+)", r.text)
        total_pages = int(page_match.group(1)) if page_match else 1
        state_match = _GRID_STATE_RE.search(r.text)
        base_form = self._build_base_form(soup)
        for page_num in range(1, total_pages if state_match else 1):
            if state_match is None:
                break
            state = state_match.group(1)
            arg = f"PN{page_num}"
            inner = f"12|PAGERONCLICK{len(arg)}|{arg}"
            data = dict(base_form)
            data[_FORM + "dgvPickUpDates"] = (
                "{&quot;keys&quot;:[],&quot;callbackState&quot;:&quot;"
                + state
                + "&quot;,&quot;selection&quot;:&quot;&quot;}"
            )
            data["__CALLBACKID"] = _FORM + "dgvPickUpDates"
            data["__CALLBACKPARAM"] = f"c0:KV|2;[];GB|{len(inner)};{inner};"
            r = session.post(self._page_url, data=data)
            r.raise_for_status()
            responses.append(r)
            state_match = _CALLBACK_STATE_RE.search(r.text) or state_match
        return responses

    def parse(self, responses):
        entries = self._parse_grid_page(BeautifulSoup(responses[0].text, "html.parser"))
        for response in responses[1:]:
            entries.extend(self._parse_grid_fragment(response.text))
        if not entries:
            raise SourceArgumentException(
                "strasse",
                "No collection dates found. The provider may not publish any schedule data at the moment, or the address parameters are incorrect.",
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
