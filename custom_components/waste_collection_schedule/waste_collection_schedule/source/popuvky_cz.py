import html as html_lib
import re
from datetime import date

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Popůvky"
DESCRIPTION = (
    "Source for the municipal waste collection calendar of Popůvky, Czech Republic."
)
URL = "https://www.popuvky.cz/obec/terminy-svozu/"
COUNTRY = "cz"

TEST_CASES = {
    "Popůvky (Brno-venkov)": {"place": "Popůvky (Brno-venkov)"},
    "Popůvky - chatová oblast": {"place": "Popůvky - chatová oblast"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open the collection calendar page and note which collection route matches "
        "your address: 'Popůvky (Brno-venkov)' for the village itself, or "
        "'Popůvky - chatová oblast' for the cottage/recreational area."
    ),
    "de": (
        "Öffnen Sie die Abfuhrkalender-Seite und notieren Sie, welche Route zu Ihrer "
        "Adresse passt: 'Popůvky (Brno-venkov)' für den Ort selbst oder "
        "'Popůvky - chatová oblast' für das Hüttengebiet."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "place": "Collection route/area exactly as listed on the official calendar page",
    },
    "de": {
        "place": "Abfuhrgebiet/-route, genau wie auf der offiziellen Kalenderseite aufgeführt",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "place": "Collection area",
    },
    "de": {
        "place": "Abfuhrgebiet",
    },
}

ICON_MAP = {
    "Komunální odpad": Icons.GENERAL_WASTE,
    "Plasty od domu": Icons.PLASTIC_PACKAGING,
    "Papír": Icons.PAPER,
    "Sklo": Icons.GLASS,
    "BIO odpad od domu": Icons.ORGANIC,
}

PAGE_URL = "https://www.popuvky.cz/obec/terminy-svozu/"
API_URL = "https://www.popuvky.cz/modules/communal_services/ax_calendar.php"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Number of months (starting with the current one) to fetch. Covers a full
# rolling year, similar to other calendar-widget-based sources.
MONTHS_TO_FETCH = 13

PLACE_SELECT_RE = re.compile(
    r'<select name="communal_place"[^>]*>(.*?)</select>', re.DOTALL
)
OPTION_RE = re.compile(r"<option[^>]*value=['\"](\d+)['\"][^>]*>([^<]*)</option>")
ACTIVE_RE = re.compile(r"active:\s*(\d+)")
TOOLTIP_RE = re.compile(
    r'<div class="sr-only" id="com-tooltip(\d{4})(\d{2})(\d{2})">\s*<dl>(.*?)</dl>',
    re.DOTALL,
)
DT_RE = re.compile(r"<dt>(.*?)</dt>", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


class Source:
    def __init__(self, place: str):
        self._place = place.strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        r = session.get(PAGE_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        page_html = r.text

        places = _parse_places(page_html)
        if not places:
            raise ValueError(
                "Could not find any collection routes on the Popůvky waste calendar "
                "page. The website layout may have changed."
            )

        place_id = None
        for name, pid in places.items():
            if name.casefold() == self._place.casefold():
                place_id = pid
                break
        if place_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "place", self._place, list(places.keys())
            )

        active_match = ACTIVE_RE.search(page_html)
        if not active_match:
            raise ValueError(
                "Could not determine the waste-calendar widget id from the Popůvky "
                "website. The website layout may have changed."
            )
        active_id = active_match.group(1)

        entries: list[Collection] = []
        today = date.today()
        year, month = today.year, today.month
        for _ in range(MONTHS_TO_FETCH):
            params = {
                "communal_month": month,
                "communal_year": year,
                "active": active_id,
                "communal_place": place_id,
                "communal_waste": 0,
            }
            resp = session.get(API_URL, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            entries.extend(_parse_month(resp.text, year, month))

            month += 1
            if month > 12:
                month = 1
                year += 1

        return entries


def _parse_places(page_html: str) -> dict[str, str]:
    select_match = PLACE_SELECT_RE.search(page_html)
    if not select_match:
        return {}
    places: dict[str, str] = {}
    for pid, name in OPTION_RE.findall(select_match.group(1)):
        name = name.strip()
        if name:
            places[name] = pid
    return places


def _parse_month(month_html: str, year: int, month: int) -> list[Collection]:
    entries: list[Collection] = []
    for year_s, month_s, day_s, dl_content in TOOLTIP_RE.findall(month_html):
        # The rendered grid also contains a few overflow days from the
        # previous/next month to fill out the week rows. Skip those here;
        # they are (and will be) picked up when that month is fetched.
        if int(year_s) != year or int(month_s) != month:
            continue
        collection_date = date(int(year_s), int(month_s), int(day_s))
        for dt in DT_RE.findall(dl_content):
            waste_type = TAG_RE.sub("", dt)
            waste_type = html_lib.unescape(waste_type)
            waste_type = re.sub(r"\s+", " ", waste_type).strip()
            if not waste_type:
                continue
            entries.append(
                Collection(
                    collection_date,
                    waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )
    return entries
