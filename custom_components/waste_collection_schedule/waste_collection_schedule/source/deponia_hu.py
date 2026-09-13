"""Depónia Nonprofit Kft. (Hungary) waste collection source.

Schedules are published as annual PowerPoint-exported PDFs behind the Drupal
settlement search form at https://deponia.hu/telepuleskereso. Smaller towns
get a single city-level calendar; larger towns require a street selection
that maps onto a street-level PDF.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import date, timedelta
from io import BytesIO
from typing import Any
from urllib.parse import unquote, urljoin

import requests
import urllib3
from bs4 import BeautifulSoup
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)

TITLE = "Depónia Nonprofit Kft."
DESCRIPTION = (
    "Source for Depónia Nonprofit Kft. waste calendars "
    "(Fejér, Veszprém and Komárom-Esztergom counties, Hungary)."
)
URL = "https://deponia.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Aba (city calendar)": {"city": "Aba", "ssl_verify": False},
    "Nadap (city calendar)": {"city": "Nadap", "ssl_verify": False},
    "Etyek (city calendar, holiday move)": {"city": "Etyek", "ssl_verify": False},
    "Székesfehérvár Fő utca": {
        "city": "Székesfehérvár",
        "street": "Fő utca",
        "ssl_verify": False,
    },
    "Velence Adria körút": {
        "city": "Velence",
        "street": "Adria körút",
        "ssl_verify": False,
    },
}

SOURCE_CODEOWNERS = ["@tothi"]

SEARCH_URL = "https://deponia.hu/telepuleskereso"
AJAX_URL = "https://deponia.hu/telepuleskereso?ajax_form=1"

ICON_MAP = {
    "Communal": Icons.GENERAL_WASTE,
    "Selective": Icons.RECYCLING,
    "Green": Icons.GARDEN,
    "Kitchen": Icons.BIO_KITCHEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://deponia.hu/telepuleskereso and pick your settlement. "
        "If a street dropdown appears, copy the street name exactly as listed "
        "(including house-number ranges such as 'Ady Endre utca 1-20.'). "
        "Smaller settlements have a single calendar and do not need a street."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Settlement name as shown on deponia.hu/telepuleskereso.",
        "street": (
            "Street name as shown after selecting the settlement. "
            "Required only for towns that publish street-level calendars."
        ),
        "ssl_verify": "Verify the HTTPS certificate. Set to false only if your environment cannot validate deponia.hu.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "Settlement",
        "street": "Street",
        "ssl_verify": "Verify SSL certificate",
    },
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.8",
}

_AJAX_HEADERS = {
    **_HEADERS,
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": SEARCH_URL,
}

_MONTHS = {
    "január": 1,
    "február": 2,
    "március": 3,
    "április": 4,
    "május": 5,
    "június": 6,
    "július": 7,
    "augusztus": 8,
    "szeptember": 9,
    "október": 10,
    "november": 11,
    "december": 12,
}

_WEEKDAYS = {
    "hétfő": 0,
    "kedd": 1,
    "szerda": 2,
    "csütörtök": 3,
    "péntek": 4,
    "szombat": 5,
    "vasárnap": 6,
}

_TYPE_MAP = {
    "szelektív": "Selective",
    "zöldhulladék": "Green",
    "konyhai": "Kitchen",
}

_TYPE_RE = re.compile(r"\b(szelektív|zöldhulladék|konyhai)\b", re.IGNORECASE)
_SKIP_ROW_RE = re.compile(r"gyűjtés:|gyűjtésbe|gyűjtést|anyagok", re.IGNORECASE)
_YEAR_RE = re.compile(r"(20\d{2})\.\s*évi\s+hulladéknaptár", re.IGNORECASE)
_VEGYES_RE = re.compile(r"Vegyes\s+hulladékgyűjtési\s+nap\s*:?\s*(.*)", re.IGNORECASE)
_CELL_RE = re.compile(
    r"-|"
    r"\d{1,2}(?:\.,\d{1,2}){1,3}\.?|"
    r"\d{1,2}[.,]\s{1,2}\d{1,2}|"
    r"\d{1,2}\.\d{1,2}\.?|"
    r"\d{1,2}\.?"
)
_DAY_RE = re.compile(r"\d{1,2}")
_ISO_POSTPONE_RE = re.compile(
    r"(20\d{2})\.(\d{2})\.(\d{2})\.[^.]*?áthelyezésre kerül\s*"
    r"(20\d{2})\.(\d{2})\.(\d{2})",
    re.IGNORECASE,
)
_HU_POSTPONE_RE = re.compile(
    r"áthelyezés:\s*(\w+)\s+(\d{1,2})\.\s*gyűjtés\s*(\w+)\s+(\d{1,2})",
    re.IGNORECASE,
)


def _norm(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", stripped).strip().casefold()


def _match_named(
    argument: str,
    needle: str | None,
    options: list[tuple[str, str]],
) -> str:
    """Return the form value of a dropdown option matching ``needle``."""
    labels = [label for _, label in options]
    if not needle:
        raise SourceArgumentRequiredWithSuggestions(
            argument,
            f"{argument} is required for this settlement.",
            labels,
        )

    wanted = _norm(needle)
    exact = [(value, label) for value, label in options if _norm(label) == wanted]
    if len(exact) == 1:
        return exact[0][0]
    if len(exact) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            argument, needle, [label for _, label in exact]
        )

    partial = [
        (value, label)
        for value, label in options
        if wanted in _norm(label) or _norm(label).startswith(wanted)
    ]
    if len(partial) == 1:
        return partial[0][0]
    if len(partial) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            argument, needle, [label for _, label in partial]
        )
    raise SourceArgumentNotFoundWithSuggestions(argument, needle, labels)


def _parse_drupal_settings(html: str) -> dict[str, Any]:
    match = re.search(
        r'<script type="application/json" data-drupal-selector="drupal-settings-json">(.*?)</script>',
        html,
    )
    if not match:
        raise Exception("Could not read Drupal page state from deponia.hu.")
    return json.loads(match.group(1))


def _ajax_post(
    session: requests.Session,
    *,
    form_id: str,
    honeypot: str,
    build_id: str,
    ajax_page_state: dict[str, Any],
    trigger: str,
    extra: dict[str, str],
    verify: bool,
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    data = {
        "form_build_id": build_id,
        "form_id": form_id,
        "honeypot_time": honeypot,
        "link": "",
        "_triggering_element_name": trigger,
        "ajax_page_state[theme]": ajax_page_state.get("theme", "basic"),
        "ajax_page_state[theme_token]": ajax_page_state.get("theme_token") or "",
        "ajax_page_state[libraries]": ajax_page_state.get("libraries", ""),
    }
    data.update(extra)
    response = session.post(
        AJAX_URL,
        data=data,
        headers=_AJAX_HEADERS,
        timeout=30,
        verify=verify,
    )
    response.raise_for_status()
    try:
        commands = response.json()
    except ValueError as exc:
        raise Exception("deponia.hu returned a non-JSON AJAX response.") from exc

    new_id = build_id
    new_state = ajax_page_state
    for command in commands:
        if command.get("command") == "update_build_id":
            new_id = command["new"]
        elif command.get("command") == "settings":
            settings = command.get("settings") or {}
            if "ajaxPageState" in settings:
                new_state = settings["ajaxPageState"]
    return commands, new_id, new_state


def _iter_insert_soups(commands: list[dict[str, Any]]) -> list[BeautifulSoup]:
    soups = []
    for command in commands:
        if command.get("command") != "insert" or not command.get("data"):
            continue
        soups.append(BeautifulSoup(command["data"], "html.parser"))
    return soups


def _extract_streets(commands: list[dict[str, Any]]) -> list[tuple[str, str]]:
    streets: list[tuple[str, str]] = []
    for soup in _iter_insert_soups(commands):
        select = soup.find("select", {"name": "utca"})
        if select is None:
            continue
        for option in select.find_all("option"):
            value = option.get("value") or ""
            label = option.get_text(strip=True)
            if value:
                streets.append((value, label))
    return streets


def _extract_calendar_links(
    commands: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for soup in _iter_insert_soups(commands):
        for anchor in soup.find_all("a"):
            href = anchor.get("href") or ""
            text = anchor.get_text(" ", strip=True)
            blob = _norm(unquote(href) + " " + text)
            href_l = unquote(href).lower()
            if "/tk_dijak/" in href_l or "dij" in blob:
                continue
            if "naptar" in blob or "hulladeknaptar" in blob:
                links.append((urljoin(URL, href), text))
    return links


def _weekdays_from_text(text: str) -> list[int]:
    folded = _norm(text)
    found = [wd for name, wd in _WEEKDAYS.items() if _norm(name) in folded]
    return sorted(set(found))


def _parse_weekdays(text: str) -> list[int]:
    for line in text.splitlines():
        match = _VEGYES_RE.search(line)
        if not match:
            continue
        rest = re.split(r"k[eé]rj[uü]k|20\d{2}", match.group(1), flags=re.IGNORECASE)[0]
        return _weekdays_from_text(rest)
    return []


def _parse_postponements(text: str, year: int) -> list[tuple[date, date]]:
    moves: list[tuple[date, date]] = []
    for match in _ISO_POSTPONE_RE.finditer(text):
        src = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        dst = date(int(match.group(4)), int(match.group(5)), int(match.group(6)))
        moves.append((src, dst))
    for match in _HU_POSTPONE_RE.finditer(text):
        src_month = _MONTHS.get(match.group(1).lower())
        dst_month = _MONTHS.get(match.group(3).lower())
        if not src_month or not dst_month:
            continue
        try:
            src = date(year, src_month, int(match.group(2)))
            dst = date(year, dst_month, int(match.group(4)))
        except ValueError:
            continue
        moves.append((src, dst))
    return moves


def _month_columns(line: str) -> list[tuple[int, int]] | None:
    low = line.lower()
    if "január" not in low or "december" not in low:
        return None
    cols: list[tuple[int, int]] = []
    for name, number in _MONTHS.items():
        pos = low.find(name)
        if pos >= 0:
            cols.append((pos, number))
    cols.sort()
    return cols if len(cols) == 12 else None


def _assign_month(pos: int, month_cols: list[tuple[int, int]]) -> int:
    return min(month_cols, key=lambda col: abs(col[0] - pos))[1]


def _parse_type_row(
    line: str, year: int, month_cols: list[tuple[int, int]]
) -> list[tuple[date, str]]:
    if _SKIP_ROW_RE.search(line):
        return []
    match = _TYPE_RE.search(line)
    if not match:
        return []
    after = line[match.end() :]
    if not re.search(r"\d|-", after):
        return []
    waste_type = _TYPE_MAP[match.group(1).lower()]
    entries: list[tuple[date, str]] = []
    for cell in _CELL_RE.finditer(after):
        token = cell.group()
        if token in ("-", "–", "—") or not _DAY_RE.search(token):
            continue
        month = _assign_month(match.end() + cell.start(), month_cols)
        for day in (int(item) for item in _DAY_RE.findall(token)):
            try:
                entries.append((date(year, month, day), waste_type))
            except ValueError:
                _LOGGER.debug("Ignoring invalid date %s-%s-%s", year, month, day)
    return entries


def _dates_for_weekdays(year: int, weekdays: list[int]) -> list[date]:
    cursor = date(year, 1, 1)
    end = date(year, 12, 31)
    result: list[date] = []
    while cursor <= end:
        if cursor.weekday() in weekdays:
            result.append(cursor)
        cursor += timedelta(days=1)
    return result


def _apply_postponements(
    dates: list[date], moves: list[tuple[date, date]]
) -> list[date]:
    remaining = set(dates)
    for src, dst in moves:
        if src in remaining:
            remaining.remove(src)
            remaining.add(dst)
    return sorted(remaining)


def parse_calendar_pdf(
    content: bytes, extra_weekday_text: str = ""
) -> list[Collection]:
    """Parse a Depónia hulladéknaptár PDF into collection events."""
    reader = PdfReader(BytesIO(content))
    layout_parts: list[str] = []
    plain_parts: list[str] = []
    for page in reader.pages:
        layout_parts.append(page.extract_text(extraction_mode="layout") or "")
        plain_parts.append(page.extract_text() or "")
    layout = "\n".join(layout_parts)
    plain = "\n".join(plain_parts)
    combined = f"{layout}\n{plain}\n{extra_weekday_text}"

    year_match = _YEAR_RE.search(combined)
    if not year_match:
        raise Exception("Could not read the calendar year from the Depónia PDF.")
    year = int(year_match.group(1))

    month_cols = None
    for line in layout.splitlines():
        month_cols = _month_columns(line)
        if month_cols:
            break
    if not month_cols:
        raise Exception("Could not find the month table in the Depónia PDF.")

    dated: list[tuple[date, str]] = []
    for line in layout.splitlines():
        dated.extend(_parse_type_row(line, year, month_cols))

    weekdays = _parse_weekdays(combined)
    if not weekdays:
        weekdays = _weekdays_from_text(extra_weekday_text)

    moves = _parse_postponements(combined, year)
    if weekdays:
        for when in _apply_postponements(_dates_for_weekdays(year, weekdays), moves):
            dated.append((when, "Communal"))

    if not dated:
        raise Exception("No collection dates could be extracted from the Depónia PDF.")

    return [
        Collection(when, waste_type, icon=ICON_MAP.get(waste_type))
        for when, waste_type in dated
    ]


class Source:
    def __init__(
        self,
        city: str,
        street: str | None = None,
        ssl_verify: bool = True,
    ) -> None:
        self._city = city
        self._street = street
        self._ssl_verify = ssl_verify

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(_HEADERS)

        response = session.get(SEARCH_URL, timeout=30, verify=self._ssl_verify)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.find("form", id="telepuleskereso-form")
        if form is None:
            raise Exception("Could not find the settlement search form on deponia.hu.")

        fields = {
            inp["name"]: inp.get("value") or ""
            for inp in form.find_all("input")
            if inp.get("name")
        }
        city_select = form.find("select", {"name": "telepules"})
        if city_select is None:
            raise Exception("Could not find the settlement list on deponia.hu.")
        cities = [
            (option.get("value") or "", option.get_text(strip=True))
            for option in city_select.find_all("option")
            if option.get("value")
        ]
        city_id = _match_named("city", self._city, cities)

        settings = _parse_drupal_settings(response.text)
        ajax_state = settings["ajaxPageState"]
        commands, build_id, ajax_state = _ajax_post(
            session,
            form_id=fields["form_id"],
            honeypot=fields["honeypot_time"],
            build_id=fields["form_build_id"],
            ajax_page_state=ajax_state,
            trigger="telepules",
            extra={"telepules": city_id},
            verify=self._ssl_verify,
        )

        streets = _extract_streets(commands)
        calendar_links = _extract_calendar_links(commands)

        if streets:
            street_value = _match_named("street", self._street, streets)
            commands, _, _ = _ajax_post(
                session,
                form_id=fields["form_id"],
                honeypot=fields["honeypot_time"],
                build_id=build_id,
                ajax_page_state=ajax_state,
                trigger="utca",
                extra={"telepules": city_id, "utca": street_value},
                verify=self._ssl_verify,
            )
            calendar_links = _extract_calendar_links(commands)

        if not calendar_links:
            raise Exception(
                f"No waste calendar PDF was returned for {self._city}"
                + (f", {self._street}" if self._street else "")
                + "."
            )

        pdf_url, link_text = calendar_links[0]
        pdf = session.get(pdf_url, timeout=60, verify=self._ssl_verify)
        pdf.raise_for_status()
        if b"%PDF" not in pdf.content[:16]:
            raise Exception(f"Depónia calendar download was not a PDF: {pdf_url}")

        extra_weekdays = ""
        paren = re.search(r"\(([^)]+)\)", link_text)
        if paren and "szelektív" not in paren.group(1).lower():
            extra_weekdays = paren.group(1)

        return parse_calendar_pdf(pdf.content, extra_weekday_text=extra_weekdays)
