import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "myWasteWatcher (WasteWatcher.NET)"
DESCRIPTION = (
    "Source for mywastewatcher.de (WasteWatcher.NET) waste collection schedules."
)
URL = "https://www.mywastewatcher.de"
COUNTRY = "de"
SOURCE_CODEOWNERS = ["@ItsMly"]

TEST_CASES = {
    "Hamminkeln, Molkereistraße (default oguid/app_path)": {
        "ort": "Hamminkeln",
        "strasse": "Molkereistraße",
    },
    "Hamminkeln, Ackerstraße Mehrhoog": {
        "oguid": "B3E02353-2090-4EFA-B3C7-AEC81FBC1E6F",
        "app_path": "abfallkalenderdk",
        "ort": "Hamminkeln",
        "strasse": "Ackerstraße",
        "ortsteil": "Mehrhoog",
    },
    "Hamminkeln, Marktstraße": {
        "oguid": "B3E02353-2090-4EFA-B3C7-AEC81FBC1E6F",
        "app_path": "abfallkalenderdk",
        "ort": "Hamminkeln",
        "strasse": "Marktstraße",
    },
    "Hamminkeln, dropdown label": {
        "strasse": "Ackerstraße (Mehrhoog)",
    },
}

# Grid rows carry short fraction codes with a tour suffix (e.g. "LP HAM02"),
# so lookups fall back to the first token of the waste-type string.
ICON_MAP = {
    "restabfall": Icons.GENERAL_WASTE,
    "restmüll": Icons.GENERAL_WASTE,
    "ra": Icons.GENERAL_WASTE,
    "bioabfall": Icons.ORGANIC,
    "biomüll": Icons.ORGANIC,
    "ba": Icons.ORGANIC,
    "papier": Icons.PAPER,
    "papier, pappe, karton": Icons.PAPER,
    "altpapier": Icons.PAPER,
    "pa": Icons.PAPER,
    "leichtverpackung": Icons.PLASTIC_PACKAGING,
    "leichtverpackungen": Icons.PLASTIC_PACKAGING,
    "gelbe tonne": Icons.PLASTIC_PACKAGING,
    "gelber sack": Icons.PLASTIC_PACKAGING,
    "lp": Icons.PLASTIC_PACKAGING,
    "glas": Icons.GLASS,
    "glasverpackungen": Icons.GLASS,
    "gl": Icons.GLASS,
    "grünschnitt": Icons.GARDEN,
    "gb": Icons.GARDEN,
    "schadstoffe": Icons.HAZARDOUS,
    "schadstoffmobil": Icons.HAZARDOUS,
    "sc": Icons.HAZARDOUS,
    "sperrmüll": Icons.BULKY,
    "sp": Icons.BULKY,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "The pre-filled oguid and app_path select Hamminkeln — then just enter "
        "city and street exactly as shown on the website. For another "
        "municipality, open its calendar page on https://www.mywastewatcher.de "
        "(e.g. via the link from your local waste authority): the first path "
        "segment of the URL is the app_path (e.g. 'abfallkalenderdk'), and the "
        "oguid is the value of the 'oguid' parameter in the URL."
    ),
    "de": (
        "Die vorausgefüllten Werte für oguid und app_path wählen Hamminkeln aus "
        "— dann nur noch Ort und Straße genau wie auf der Webseite angezeigt "
        "eingeben. Für eine andere Kommune deren Abfallkalender-Seite auf "
        "https://www.mywastewatcher.de öffnen (z.B. über den Link des "
        "Entsorgungsbetriebs): Das erste Pfad-Segment der URL ist der App-Pfad "
        "(z.B. 'abfallkalenderdk'), die OGUID ist der Wert des URL-Parameters "
        "'oguid'."
    ),
}

PARAM_TRANSLATIONS = {
    "de": {
        "oguid": "OGUID (Kennung des Entsorgungsgebiets)",
        "app_path": "App-Pfad (z.B. abfallkalenderdk)",
        "ort": "Ort",
        "strasse": "Straße",
        "ortsteil": "Ortsteil",
        "bemerkung": "Bemerkung (z.B. Hausnummern)",
    },
    "en": {
        "oguid": "OGUID (waste management area identifier)",
        "app_path": "App path (e.g. abfallkalenderdk)",
        "ort": "City",
        "strasse": "Street",
        "ortsteil": "District",
        "bemerkung": "Remark (e.g. house numbers)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "oguid": "Unique identifier for the waste management area (OGUID), visible in the URL of the provider's page. The default selects Hamminkeln.",
        "app_path": "Path segment of the provider URL (e.g. 'abfallkalenderdk'). The default selects Hamminkeln.",
        "ort": "City name exactly as shown on the website.",
        "strasse": "Street name exactly as shown on the website.",
        "ortsteil": "District name (optional), used when multiple districts share the same street name.",
        "bemerkung": "Remark field shown in the street list (e.g. house number ranges like '1-50'). Use when multiple entries exist for the same street.",
    },
    "de": {
        "oguid": "Eindeutige Kennung des Entsorgungsgebiets (OGUID), in der URL der Anbieterseite sichtbar. Der Standardwert wählt Hamminkeln aus.",
        "app_path": "Pfad-Segment der Anbieter-URL (z.B. 'abfallkalenderdk'). Der Standardwert wählt Hamminkeln aus.",
        "ort": "Ortsname genau wie auf der Webseite angezeigt.",
        "strasse": "Straßenname genau wie auf der Webseite angezeigt.",
        "ortsteil": "Ortsteil (optional), wenn mehrere Ortsteile denselben Straßennamen haben.",
        "bemerkung": "Bemerkungsfeld aus der Straßenliste (z.B. Hausnummernbereiche wie '1-50'). Angeben, wenn mehrere Einträge für dieselbe Straße existieren.",
    },
}

BASE_URL = "https://www.mywastewatcher.de/{app_path}/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.mywastewatcher.de/",
}

_FORM = "ctl00$MainContent$frmKalender$"
_FORM_ID = "ctl00_MainContent_frmKalender_"

_DATA_ROW_RE = re.compile(r"<tr[^>]*class=\"[^\"]*dxgvDataRow.*?</tr>", re.DOTALL)
_CELL_RE = re.compile(r"<td.*?</td>", re.DOTALL)
_CALLBACK_STATE_RE = re.compile(r"'callbackState':'([^']+)'")
_GRID_STATE_RE = re.compile(
    r"ASPxClientGridView,'" + _FORM_ID + r"dgvPickUpDates'.*?'callbackState':'([^']+)'",
    re.DOTALL,
)


class Source:
    # The defaults select Hamminkeln, currently the only instance that
    # publishes schedule data. The abfallkalenderdk2 (Kalkar) and
    # abfallkalenderRBE (Rheinberg) instances exist but return "Keine Daten
    # zum Anzeigen" for every street (checked 2026-07).
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
            if not name:
                continue
            itype = inp.get("type", "text")
            if itype == "hidden":
                data[name] = inp.get("value", "")
            elif itype == "text":
                val = inp.get("value", "")
                # Only include non-empty or DevExpress state fields
                if val or "State" in name or "_VI" in name or "DDD" in name:
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

        # Extract itemsValue GUIDs from the JS createControl call
        match = re.search(
            r"createControl\(ASPxClientListBox,'" + _FORM_ID + r"cboStreets_DDD_L'"
            r".*?'itemsValue':\[([^\]]+)\]",
            html,
            re.DOTALL,
        )
        if not match:
            return None, []
        guids = re.findall(
            r"'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'",
            match.group(1),
            re.I,
        )

        # Extract street name rows from the HTML table (same order as GUIDs)
        table = soup.find("table", {"id": _FORM_ID + "cboStreets_DDD_L_LBT"})
        if not table:
            return None, []
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

            # Build a human-readable label for the suggestions list
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

            return guids[i], all_streets

        return None, all_streets

    def _split_street_label(self) -> bool:
        """Split a combined "Street (Ortsteil) – Bemerkung" suggestion label.

        The config flow re-offers the labels built in _find_street_guid as a
        dropdown when the street was not found; accept a picked label as
        strasse input by splitting it back into its parts.
        Returns True if strasse was changed.
        """
        match = re.fullmatch(r"(.+?)(?: \(([^()]+)\))?(?: – (.+))?", self._strasse)
        if not match or (not match.group(2) and not match.group(3)):
            return False
        self._strasse = match.group(1)
        self._ortsteil = self._ortsteil or match.group(2) or ""
        self._bemerkung = self._bemerkung or match.group(3) or ""
        return True

    def _collection(
        self, bin_type: str, date_str: str, description: str | None
    ) -> Collection | None:
        try:
            day = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            return None
        icon = ICON_MAP.get(bin_type.lower())
        if icon is None:
            # "LP HAM02" style entries: fraction code plus tour suffix
            icon = ICON_MAP.get(bin_type.split()[0].lower())
        return Collection(day, bin_type, icon, description=description)

    def _parse_grid_page(self, soup: BeautifulSoup) -> list[Collection]:
        """Parse the dgvPickUpDates grid of a full page into Collection entries."""
        entries: list[Collection] = []
        table = soup.find("table", {"id": re.compile(r"dgvPickUpDates_DXMainTable")})
        if not table:
            return entries

        for row in table.find_all("tr"):
            cls = " ".join(row.get("class", []))
            if "dxgvDataRow" not in cls:
                continue
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            entries.extend(self._entries_from_cells(cells))
        return entries

    def _parse_grid_fragment(self, text: str) -> list[Collection]:
        """Parse grid rows out of a DevExpress callback response.

        The callback payload wraps the grid HTML in a JavaScript string that
        html.parser cannot digest as a whole, so the data rows are extracted
        with regexes and parsed individually.
        """
        entries: list[Collection] = []
        for row_html in _DATA_ROW_RE.findall(text):
            cells = [
                BeautifulSoup(cell, "html.parser").get_text(strip=True)
                for cell in _CELL_RE.findall(row_html)
            ]
            entries.extend(self._entries_from_cells(cells))
        return entries

    def _entries_from_cells(self, cells: list[str]) -> list[Collection]:
        # Columns: Farbe/Symbol | Abfallart/Bezirk | Abfuhrtag | Wochentag | V | Bemerkung
        if len(cells) < 3:
            return []
        bin_type, date_str = cells[1], cells[2]
        if not bin_type or not date_str:
            return []
        # Bemerkung carries e.g. the stops and times of the Schadstoffmobil
        description = cells[5] if len(cells) > 5 else None
        collection = self._collection(bin_type, date_str, description or None)
        return [collection] if collection else []

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(_HEADERS)

        soup = self._select_city(session)

        # The street dropdown only lists streets starting with the letter
        # selected in the "Beginnt mit" combo (defaults to "A"), so switch
        # the filter to the street's first letter before looking it up.
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
            # A "Beginnt mit" postback leaves state behind that makes the
            # grid paging callbacks below return empty pages, so restart
            # with a clean session now that the street GUID is known.
            session = requests.Session()
            session.headers.update(_HEADERS)
            soup = self._select_city(session)

        # Select the street ...
        data = self._build_base_form(soup)
        data["__EVENTTARGET"] = _FORM + "cboStreets"
        data["__EVENTARGUMENT"] = ""
        data[_FORM_ID + "cboStreets_VI"] = street_guid
        data[_FORM + "cboStreets"] = self._strasse
        data[_FORM + "cboStreets$DDD$L"] = street_guid
        soup = self._parse_response(session.post(self._page_url, data=data))

        # ... and press "Termine abrufen", which binds the result grid
        btn = soup.find("input", {"id": _FORM_ID + "btnTermineHolen_I"})
        data = self._build_base_form(soup)
        if btn is not None:
            data[btn["name"]] = btn.get("value") or "Termine abrufen"
        r = session.post(self._page_url, data=data)
        soup = self._parse_response(r)

        entries = self._parse_grid_page(soup)

        # Remaining grid pages are served via DevExpress callbacks. Each
        # request must carry the grid's client state (from the createControl
        # JS; refreshed from every callback response) including the
        # "selection" key — without it the server discards the state and
        # returns an empty grid.
        page_match = re.search(r"Seite \d+ von (\d+)", r.text)
        total_pages = int(page_match.group(1)) if page_match else 1
        state_match = _GRID_STATE_RE.search(r.text)
        base_form = self._build_base_form(soup)

        for page_num in range(1, total_pages if state_match else 1):
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
            entries.extend(self._parse_grid_fragment(r.text))
            state_match = _CALLBACK_STATE_RE.search(r.text) or state_match

        if not entries:
            raise SourceArgumentException(
                "strasse",
                "No collection dates found. The provider may not publish any "
                "schedule data at the moment, or the address parameters are "
                "incorrect.",
            )

        return entries
