"""Source for Gemeinde Seuzach, Switzerland."""

import json
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Gemeinde Seuzach"
DESCRIPTION = "Source for waste collection services in Seuzach, Switzerland."
URL = "https://www.seuzach.ch"
COUNTRY = "ch"
TEST_CASES: dict[str, dict] = {
    "Seuzach": {},
}

BASE_URL = "https://www.seuzach.ch"
EVENTS_URL = f"{BASE_URL}/abfalldaten"

# The website publishes two kinds of data, both fetched live on every run --
# nothing about the actual schedule is hardcoded:
#
# - "Regelmässige Abfuhr" (regular collections: Kehrichtabfuhr, Grünabfuhr):
#   not published as a list of dates. Each runs weekly on a fixed German
#   weekday, described only in prose on a linked detail page (e.g. "findet
#   wöchentlich am Dienstag statt"). Grünabfuhr additionally only runs
#   within a described season (e.g. "von März bis November ... erstmals am
#   2. März und letztmals am 30. November"). This source resolves the
#   detail-page link(s) from the events page and parses the weekday/season
#   from the live text on every fetch, rather than assuming a fixed rule.
# - "Besondere Sammeltermine" (special town-wide collections: Papier-/
#   Kartonsammlung, Sonderabfälle, Häckseldienst, and the Jan/Feb/Dec
#   Grünabfuhr dates that fall outside the regular season): published with
#   concrete dates in a table on the events page.

# How far into the future to generate the recurring weekly collections.
# Occurrences outside a collection's published season (if any) are dropped.
WEEKLY_HORIZON_DAYS = 400

WEEKDAY_RRULE = {
    "Montag": MO,
    "Dienstag": TU,
    "Mittwoch": WE,
    "Donnerstag": TH,
    "Freitag": FR,
    "Samstag": SA,
    "Sonntag": SU,
}

GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

_ICON_KEYWORDS = {
    "kehricht": Icons.GENERAL_WASTE,
    "grün": Icons.GARDEN,
    "papier": Icons.PAPER,
    "karton": Icons.PAPER,
    "sonderabf": Icons.HAZARDOUS,
    "häcksel": Icons.GARDEN,
}

_TAG_RE = re.compile(r"<[^>]+>")
_DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
_WEEKDAY_RE = re.compile(
    r"wöchentlich\s+am\s+(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)"
)
_SEASON_RE = re.compile(
    r"erstmals am (\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)(?:\s+(\d{4}))?"
    r".*?"
    r"letztmals am (\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)(?:\s+(\d{4}))?",
    re.DOTALL,
)


def _strip_tags(value: str) -> str:
    return _TAG_RE.sub("", value).strip()


def _normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def _icon_for(name: str) -> Icons | None:
    lname = name.lower()
    for keyword, icon in _ICON_KEYWORDS.items():
        if keyword in lname:
            return icon
    return None


def _parse_season(text: str) -> tuple[int, int, int, int] | None:
    """Return (start_month, start_day, end_month, end_day) if the text
    describes a limited collection season (e.g. Grünabfuhr, March-November),
    or None if the collection runs all year (e.g. Kehrichtabfuhr).
    """
    match = _SEASON_RE.search(text)
    if not match:
        return None
    start_day, start_month_name, _start_year, end_day, end_month_name, _end_year = (
        match.groups()
    )
    start_month = GERMAN_MONTHS.get(start_month_name.lower())
    end_month = GERMAN_MONTHS.get(end_month_name.lower())
    if start_month is None or end_month is None:
        return None
    return start_month, int(start_day), end_month, int(end_day)


def _regular_collection_entries(
    session: requests.Session, soup: BeautifulSoup
) -> list[Collection]:
    """Parse the 'Regelmässige Abfuhr' table and follow each entry's detail
    link to discover its weekday (and, if applicable, its season) live.
    """
    table = soup.find("table", attrs={"id": "regulaeresammlungen"})
    if table is None:
        return []

    data = json.loads(table.attrs["data-entities"])

    entries: list[Collection] = []
    today = date.today()
    horizon = today + timedelta(days=WEEKLY_HORIZON_DAYS)

    for item in data.get("data", []):
        link_soup = BeautifulSoup(item.get("name", ""), "html.parser")
        link = link_soup.find("a")
        if link is None or not link.get("href"):
            continue

        name = link.get_text(strip=True)
        detail_url = urljoin(BASE_URL, link["href"])

        detail_response = session.get(detail_url, timeout=30)
        detail_response.raise_for_status()
        detail_text = _normalize_ws(_strip_tags(detail_response.text))

        weekday_match = _WEEKDAY_RE.search(detail_text)
        if not weekday_match:
            # Structure changed / no recurring weekday found for this entry;
            # skip rather than guessing.
            continue
        weekday = WEEKDAY_RRULE[weekday_match.group(1)]

        season = _parse_season(detail_text)
        icon = _icon_for(name)

        for occurrence in rrule(
            WEEKLY, byweekday=weekday, dtstart=today, until=horizon
        ):
            occurrence_date = occurrence.date()
            if season is not None:
                start_month, start_day, end_month, end_day = season
                season_start = date(occurrence_date.year, start_month, start_day)
                season_end = date(occurrence_date.year, end_month, end_day)
                if not (season_start <= occurrence_date <= season_end):
                    continue
            entries.append(Collection(date=occurrence_date, t=name, icon=icon))

    return entries


def _special_collection_entries(soup: BeautifulSoup) -> list[Collection]:
    """Parse the 'Besondere Sammeltermine' table: one-off town-wide
    collection dates published with concrete dates.
    """
    table = soup.find("table", attrs={"id": "icmsTable-abfallsammlung"})
    if table is None:
        return []

    data = json.loads(table.attrs["data-entities"])

    entries: list[Collection] = []
    for item in data.get("data", []):
        name = _strip_tags(item.get("name", ""))
        date_matches = _DATE_RE.findall(item.get("_anlassDate", ""))
        if not name or not date_matches:
            continue

        try:
            collection_date = datetime.strptime(date_matches[0], "%d.%m.%Y").date()
        except ValueError:
            continue

        entries.append(Collection(date=collection_date, t=name, icon=_icon_for(name)))

    return entries


class Source:
    def __init__(self) -> None:
        pass

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        response = session.get(EVENTS_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        entries = _regular_collection_entries(session, soup)
        entries += _special_collection_entries(soup)

        if not entries:
            raise ValueError(
                "No waste collection entries found on "
                f"{EVENTS_URL}. The website structure may have changed."
            )

        return entries
