from datetime import date, datetime
from typing import Any
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Mansfield Shire Council"
DESCRIPTION = "Source for Mansfield Shire Council rubbish collection."
URL = "https://www.mansfield.vic.gov.au"
TEST_CASES = {
    "Mansfield Zoo": {
        "street_address": "1064 Mansfield-Woods Point Road MANSFIELD VIC 3722"
    },
    "Ambulance Station": {"street_address": "3 Curia Street MANSFIELD VIC 3722"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Bin": Icons.GARDEN,
}


def _normalise_address(value: str) -> str:
    return " ".join(value.split())


def _looks_like_date_text(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if "/" in text:
        return True
    return any(
        text.startswith(prefix)
        for prefix in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    )


def _parse_date(text: str) -> date | None:
    text = text.strip()
    for fmt in ("%a %d/%m/%Y", "%A %d/%m/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _resolve_icon(label: str) -> Any | None:
    if not label:
        return None
    lowered = label.lower()
    for keyword, icon in ICON_MAP.items():
        if keyword.lower() in lowered:
            return icon
    return None


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def _autocomplete(self, query: str, session: requests.Session) -> list[str]:
        url = f"{URL}/views-autocomplete-filters/waste_schedule/block_1/formatted_address/0?q={quote_plus(query)}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "python-requests",
            "Referer": f"{URL}/waste-schedule",
        }
        try:
            r = session.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            values: list[str] = []
            for item in data:
                if isinstance(item, dict) and item.get("value"):
                    values.append(item["value"])
                elif isinstance(item, str):
                    values.append(item)
            return values
        except Exception:
            return []

    def _find_formatted_address(self, session: requests.Session) -> str | None:
        queries = [self._street_address]
        parts = self._street_address.split()
        if parts:
            queries.append(parts[0])
            if len(parts) > 1:
                queries.append(parts[0] + " " + parts[1])
        for q in queries:
            candidates = self._autocomplete(q, session)
            if candidates:
                target = _normalise_address(self._street_address)
                for c in candidates:
                    if _normalise_address(c).lower() == target.lower():
                        return c
                return candidates[0]
        return None

    def fetch(self) -> list[Collection]:
        with requests.Session() as s:
            fmt_addr = self._find_formatted_address(s)
            use_addr = fmt_addr or self._street_address
            addr = quote_plus(use_addr)
            ajax_url = (
                f"{URL}/views/ajax?_wrapper_format=drupal_ajax&view_name=waste_schedule"
                f"&view_display_id=block_1&view_args=&view_path=%2Fnode%2F96"
                f"&view_base_path=waste-schedule&formatted_address={addr}"
            )
            headers = {
                "Accept": "application/json",
                "User-Agent": "python-requests",
                "Referer": f"{URL}/waste-schedule",
                "X-Requested-With": "XMLHttpRequest",
            }
            r = s.get(ajax_url, headers=headers, timeout=30)
            r.raise_for_status()
            try:
                payload = r.json()
            except ValueError:
                payload = []

        html_parts: list[str] = []
        for entry in payload:
            if isinstance(entry, dict) and entry.get("command") == "insert":
                data = entry.get("data")
                if isinstance(data, str) and data:
                    html_parts.append(data)
        html = "\n".join(html_parts)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []

        for h4 in soup.find_all("h4"):
            waste_type = h4.get_text(" ", strip=True)
            if not waste_type:
                continue

            date_text = None
            info = h4.find_next("div", class_="info")
            if info:
                for p in info.select("p"):
                    text = p.get_text(" ", strip=True)
                    if _looks_like_date_text(text):
                        date_text = text
                        break

            if not date_text:
                for sibling in h4.find_next_siblings():
                    if getattr(sibling, "name", None) == "div" and sibling.select_one(
                        "p"
                    ):
                        for p in sibling.select("p"):
                            text = p.get_text(" ", strip=True)
                            if _looks_like_date_text(text):
                                date_text = text
                                break
                        if date_text:
                            break
                    elif getattr(sibling, "name", None) == "p":
                        text = sibling.get_text(" ", strip=True)
                        if _looks_like_date_text(text):
                            date_text = text
                            break

            if not date_text:
                continue

            collection_date = _parse_date(date_text)
            if collection_date is None:
                continue
            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=_resolve_icon(waste_type),
                )
            )

        return entries
