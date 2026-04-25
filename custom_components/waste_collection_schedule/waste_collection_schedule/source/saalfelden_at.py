import json
import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Saalfelden am Steinernen Meer"
DESCRIPTION = "Source for Saalfelden am Steinernen Meer waste collection."
URL = "https://www.saalfelden.at"
COUNTRY = "at"

TEST_CASES = {
    "Achenweg 1": {"strasse": "Achenweg", "hausnummer": 1},
    "Abdeckerweg 5": {"strasse": "Abdeckerweg", "hausnummer": "5"},
    "Achenweg 4a": {"strasse": "Achenweg", "hausnummer": "4a"},
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Gelbe Tonne": "mdi:recycle",
    "Gelber Sack": "mdi:recycle",
    "Altpapier": "mdi:package-variant",
    "Papier": "mdi:package-variant",
    "Sperrmüll": "mdi:sofa",
    "Christbaum": "mdi:pine-tree",
    "Weihnachtsbaum": "mdi:pine-tree",
    "Problemstoff": "mdi:bottle-tonic-skull",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "strasse": "Street name as listed in the Saalfelden waste calendar.",
        "hausnummer": "House number as listed in the Saalfelden waste calendar.",
    },
    "de": {
        "strasse": "Straßenname wie im Saalfeldener Abfallkalender aufgelistet.",
        "hausnummer": "Hausnummer wie im Saalfeldener Abfallkalender aufgelistet.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "strasse": "Street",
        "hausnummer": "House number",
    },
    "de": {
        "strasse": "Straße",
        "hausnummer": "Hausnummer",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://www.saalfelden.at/Buergerservice/Abfallkalender, pick "
        "your street and house number from the dropdowns, and use the same "
        "values here."
    ),
    "de": (
        "Öffnen Sie https://www.saalfelden.at/Buergerservice/Abfallkalender, "
        "wählen Sie Ihre Straße und Hausnummer aus, und verwenden Sie dieselben "
        "Werte hier."
    ),
}

CALENDAR_PAGE_URL = "https://www.saalfelden.at/Buergerservice/Abfallkalender"
API_URL = "https://www.saalfelden.at/system/web/kalender.aspx"
DETAIL_ONR = "225697049"
MENU_ONR = "225696673"
MAX_PAGES = 30
LOOKAHEAD_DAYS = 365


class Source:
    def __init__(self, strasse: str, hausnummer):
        self._strasse = str(strasse).strip()
        self._hausnummer = str(hausnummer).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        page = session.get(CALENDAR_PAGE_URL, timeout=30)
        page.raise_for_status()

        typids = self._resolve_typids(page.text)

        return self._fetch_collections(session, typids)

    def _resolve_typids(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        street_select = soup.find(
            "select",
            attrs={"name": re.compile(r"boxmuellkalenderstrassedd$")},
        )
        if street_select is None:
            raise Exception("Could not locate street selector on Saalfelden page")

        name_to_id: dict[str, int] = {}
        for opt in street_select.find_all("option"):
            value = opt.get("value", "").strip()
            text = opt.get_text(strip=True)
            if value and text:
                name_to_id[text] = int(value)

        street_id = name_to_id.get(self._strasse)
        if street_id is None:
            for name, sid in name_to_id.items():
                if name.casefold() == self._strasse.casefold():
                    street_id = sid
                    self._strasse = name
                    break
        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", self._strasse, sorted(name_to_id)
            )

        strassen_arr = self._parse_strassen_arr(html)

        for entry in strassen_arr:
            if entry[0] != street_id:
                continue
            hnr_labels: list[str] = []
            for hnr in entry[1]:
                hnr_text = str(hnr[1])
                hnr_labels.append(hnr_text)
                if hnr_text.casefold() == self._hausnummer.casefold():
                    return hnr[2]
            raise SourceArgumentNotFoundWithSuggestions(
                "hausnummer", self._hausnummer, hnr_labels
            )

        raise SourceArgumentNotFoundWithSuggestions(
            "strasse", self._strasse, sorted(name_to_id)
        )

    @staticmethod
    def _parse_strassen_arr(html: str) -> list:
        match = re.search(r"var\s+strassenArr\s*=\s*", html)
        if not match:
            raise Exception("Could not locate strassenArr in page")

        start = html.find("[", match.end())
        depth = 0
        end = start
        for idx in range(start, len(html)):
            ch = html[idx]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        if depth != 0:
            raise Exception("Could not parse strassenArr (unbalanced brackets)")

        arr_js = html[start:end]
        arr_json = arr_js.replace("'", '"')
        arr_json = re.sub(r",\s*\]", "]", arr_json)
        return json.loads(arr_json)

    def _fetch_collections(
        self, session: requests.Session, typids: str
    ) -> list[Collection]:
        entries: list[Collection] = []
        seen_keys: set[tuple[str, str]] = set()
        seen_first_row: set[tuple[str, str]] = set()

        today = date.today()
        end_date = today + timedelta(days=LOOKAHEAD_DAYS)

        for page_idx in range(MAX_PAGES):
            params = {
                "detailonr": DETAIL_ONR,
                "menuonr": MENU_ONR,
                "typids": typids,
                "page": page_idx,
                "vdatum": today.strftime("%d.%m.%Y"),
                "bdatum": end_date.strftime("%d.%m.%Y"),
            }
            r = session.get(API_URL, params=params, timeout=30)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", class_="ris_table")
            if table is None:
                break

            rows = table.find_all("tr")[1:]
            page_rows: list[tuple[date, str]] = []
            for row in rows:
                tds = row.find_all("td", class_="td_kal")
                if len(tds) != 2:
                    continue
                date_match = re.match(
                    r"(\d{2}\.\d{2}\.\d{4})", tds[0].get_text(" ", strip=True)
                )
                if not date_match:
                    continue
                collection_date = datetime.strptime(
                    date_match.group(1), "%d.%m.%Y"
                ).date()
                anchor = tds[1].find("a")
                raw_type = (
                    anchor.get_text(strip=True)
                    if anchor
                    else tds[1].get_text(" ", strip=True)
                )
                waste_type = re.sub(r"\s*\(.*\)\s*$", "", raw_type).strip()
                page_rows.append((collection_date, waste_type))

            if not page_rows:
                break

            first_key = (page_rows[0][0].isoformat(), page_rows[0][1])
            if first_key in seen_first_row:
                break
            seen_first_row.add(first_key)

            for collection_date, waste_type in page_rows:
                if collection_date > end_date:
                    continue
                key = (collection_date.isoformat(), waste_type)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                icon = self._icon_for(waste_type)
                entries.append(
                    Collection(date=collection_date, t=waste_type, icon=icon)
                )

            if page_rows[-1][0] > end_date:
                break

        return entries

    @staticmethod
    def _icon_for(waste_type: str) -> str | None:
        lowered = waste_type.casefold()
        for key, icon in ICON_MAP.items():
            if key.casefold() in lowered:
                return icon
        return None
