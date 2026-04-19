import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "localcities.ch"
DESCRIPTION = "Source for waste collection schedules from localcities.ch (Switzerland)."
URL = "https://www.localcities.ch"
COUNTRY = "ch"

TEST_CASES = {
    "Volketswil - Hegnau": {
        "municipality": "volketswil",
        "municipality_id": "529",
        "zone": "Hegnau",
    },
    "Volketswil - Kindhausen, Zimikon, Gutenswil": {
        "municipality": "volketswil",
        "municipality_id": "529",
        "zone": "Kindhausen, Zimikon, Gutenswil",
    },
    "Grenchen - Zone Ost": {
        "municipality": "grenchen",
        "municipality_id": "3533",
        "zone": "Zone Ost",
    },
    "Grenchen - Zone West": {
        "municipality": "grenchen",
        "municipality_id": "3533",
        "zone": "Zone West",
    },
    "Büren an der Aare": {
        "municipality": "bueren-an-der-aare",
        "municipality_id": "849",
        "zone": "",
    },
    "Liestal - Kreis 1": {
        "municipality": "liestal",
        "municipality_id": "3833",
        "zone": "Kreis 1",
    },
    "Therwil": {
        "municipality": "therwil",
        "municipality_id": "3757",
        "zone": "",
    },
}

EXTRA_INFO = [
    {
        "title": "Volketswil",
        "url": "https://www.volketswil.ch",
        "country": "ch",
        "default_params": {
            "municipality": "volketswil",
            "municipality_id": "529",
        },
    },
    {
        "title": "Grenchen",
        "url": "https://www.grenchen.ch",
        "country": "ch",
        "default_params": {
            "municipality": "grenchen",
            "municipality_id": "3533",
        },
    },
    {
        "title": "Wangen bei Olten",
        "url": "https://www.wangen-bei-olten.ch",
        "country": "ch",
        "default_params": {
            "municipality": "wangen-bei-olten",
            "municipality_id": "3629",
        },
    },
    {
        "title": "Büren an der Aare",
        "url": "https://www.bueren.ch",
        "country": "ch",
        "default_params": {
            "municipality": "bueren-an-der-aare",
            "municipality_id": "849",
        },
    },
    {
        "title": "Liestal",
        "url": "https://www.liestal.ch",
        "country": "ch",
        "default_params": {
            "municipality": "liestal",
            "municipality_id": "3833",
        },
    },
    {
        "title": "Therwil",
        "url": "https://www.therwil.ch",
        "country": "ch",
        "default_params": {
            "municipality": "therwil",
            "municipality_id": "3757",
        },
    },
]

ICON_MAP = {
    "Altpapier": "mdi:newspaper",
    "Grünabfälle": "mdi:leaf",
    "Karton": "mdi:package-variant",
    "Altglas": "mdi:glass-fragile",
    "Altmetall": "mdi:nail",
}

BASE_URL = "https://www.localcities.ch/de/entsorgung"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit your municipality's page on localcities.ch. The municipality name and ID are in the URL (e.g. /de/entsorgung/volketswil/529). The zone is shown next to each waste collection entry on the calendar.",
    "de": "Besuchen Sie die Seite Ihrer Gemeinde auf localcities.ch. Der Gemeindename und die ID sind in der URL (z.B. /de/entsorgung/volketswil/529). Die Zone wird neben jedem Entsorgungstermin angezeigt.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Municipality URL slug (from the localcities.ch URL)",
        "municipality_id": "Municipality ID number (from the localcities.ch URL)",
        "zone": "Collection zone or locality name",
    },
    "de": {
        "municipality": "URL-Name der Gemeinde (aus der localcities.ch URL)",
        "municipality_id": "Gemeinde-ID (aus der localcities.ch URL)",
        "zone": "Sammelzone oder Ortsname",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "municipality_id": "Municipality ID",
        "zone": "Zone",
    },
    "de": {
        "municipality": "Gemeinde",
        "municipality_id": "Gemeinde-ID",
        "zone": "Zone",
    },
}

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
    ),
}


class Source:
    def __init__(self, municipality: str, municipality_id: str | int, zone: str):
        self._municipality = municipality.strip().lower()
        self._municipality_id = str(municipality_id).strip()
        self._zone = zone.strip()

    def fetch(self) -> list[Collection]:
        base_url = f"{BASE_URL}/{self._municipality}/{self._municipality_id}"
        entries: list[Collection] = []
        discovered_zones: set[str] = set()
        page = 1

        while True:
            url = base_url if page == 1 else f"{base_url}?page={page}"
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            result_list = soup.find("div", attrs={"data-js-result-list": True})
            if result_list is None:
                break

            date_rows = result_list.find_all("div", class_="row", recursive=False)
            if not date_rows:
                break

            for row in date_rows:
                date_col = row.find("div", class_="waste-calender-list__date")
                if date_col is None:
                    continue
                date_heading = date_col.find(["h2", "h3"])
                if date_heading is None:
                    continue

                date_text = date_heading.get_text(strip=True)
                today = date.today()

                if date_text == "Heute":
                    collection_date = today
                elif date_text == "Morgen":
                    collection_date = today + timedelta(days=1)
                else:
                    year = self._find_year_for_date(result_list, row)
                    try:
                        collection_date = datetime.strptime(
                            f"{date_text}.{year}", "%d.%m.%Y"
                        ).date()
                    except ValueError:
                        continue

                waste_items = row.find_all(
                    "div",
                    class_=re.compile(r"waste-calendar-list-item-small"),
                )

                for item in waste_items:
                    img = item.find("img", alt=True)
                    if not img:
                        continue

                    waste_type = img["alt"]
                    zone_text = self._extract_zone_text(item, waste_type)
                    discovered_zones.add(zone_text)

                    if zone_text == self._zone:
                        entries.append(
                            Collection(
                                date=collection_date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )

            load_more = soup.find(
                "input",
                attrs={"data-js-results-load-more-next-page": True},
            )
            if load_more is None:
                # Also check for button element
                load_more = soup.find(
                    "button",
                    attrs={"data-js-results-load-more-next-page": True},
                )
            if load_more is None:
                break

            next_page_str = load_more.get("data-js-results-load-more-next-page", "")
            try:
                next_page = int(next_page_str)
            except ValueError:
                break

            if next_page <= page:
                break
            page = next_page

        if not entries and discovered_zones:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", self._zone, sorted(discovered_zones)
            )

        return entries

    @staticmethod
    def _extract_zone_text(waste_item, waste_type: str) -> str:
        item_text = waste_item.get_text(strip=True)
        if item_text.startswith(waste_type):
            item_text = item_text[len(waste_type) :].strip()
        return item_text

    @staticmethod
    def _find_year_for_date(result_list, current_row) -> int:
        children = list(result_list.children)
        current_year = datetime.now().year
        last_year = current_year

        for child in children:
            if child == current_row:
                return last_year

            if hasattr(child, "name") and child.name == "h1":
                headline_class = child.get("class", [])
                if any("calendar-list__headline" in c for c in headline_class):
                    span = child.find("span")
                    if span:
                        try:
                            last_year = int(span.get_text(strip=True))
                        except ValueError:
                            pass

        return last_year
