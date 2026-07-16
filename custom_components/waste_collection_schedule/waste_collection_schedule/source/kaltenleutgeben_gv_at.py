import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Marktgemeinde Kaltenleutgeben"
DESCRIPTION = "Waste collection schedule for Marktgemeinde Kaltenleutgeben, Austria."
URL = "https://www.kaltenleutgeben.gv.at"
COUNTRY = "at"

TEST_CASES: dict[str, dict] = {
    # The Kaltenleutgeben waste calendar publishes a single town-wide schedule,
    # so no address is required.
    "Kaltenleutgeben": {},
}

OVERVIEW_URL = "https://www.kaltenleutgeben.gv.at/Muellkalender_NEU"

HEADERS = {"User-Agent": "Mozilla/5.0"}

_DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")

ICON_MAP = {
    "Restmüll 770l und 1.100l Gefäße": Icons.GENERAL_WASTE,
    "Restmüll 80l und 120 l Gefäße": Icons.GENERAL_WASTE,
    "Biomüll": Icons.ORGANIC,
}


class Source:
    def __init__(self) -> None:
        pass

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        r = session.get(OVERVIEW_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        overview = BeautifulSoup(r.text, "html.parser")

        # Each row of the overview table links to a detail page for one waste
        # type. The overview table itself only shows the validity period of
        # each calendar, not the individual collection dates.
        links: dict[str, str] = {}
        table = overview.find("table", class_="ris_table")
        if table is not None:
            for row in table.find_all("tr"):
                anchor = row.find("a")
                if anchor is None or not anchor.get("href"):
                    continue
                waste_type = anchor.get_text(strip=True)
                href = anchor["href"]
                if href.startswith("http"):
                    url = href
                else:
                    url = "https://www.kaltenleutgeben.gv.at/" + href.lstrip("/")
                links[waste_type] = url

        entries: list[Collection] = []
        for waste_type, url in links.items():
            entries.extend(self._fetch_detail(session, waste_type, url))

        if not entries:
            raise ValueError("Could not find any collection events.")

        return sorted(entries, key=lambda c: c.date)

    def _fetch_detail(
        self, session: requests.Session, waste_type: str, url: str
    ) -> list[Collection]:
        r = session.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        th = soup.find("th", string=lambda s: bool(s) and "Termine" in s)
        if th is None:
            return []
        td = th.find_next_sibling("td")
        if td is None:
            return []

        icon = ICON_MAP.get(waste_type)
        entries = []
        for match in _DATE_RE.finditer(td.get_text(" ", strip=True)):
            collection_date = datetime.datetime.strptime(
                match.group(), "%d.%m.%Y"
            ).date()
            entries.append(Collection(date=collection_date, t=waste_type, icon=icon))
        return entries
