import re
from typing import Any, ClassVar, final
from urllib.parse import quote, unquote, urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service import HuWasteCalendar as hu
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.siokom.hu"
_CALENDAR_URL = f"{_BASE_URL}/jaratterv/"

_TYPE_VALUE_MAP = {
    "szelektív": wt.RECYCLABLES,
    "zöldhulladék": wt.GARDEN_WASTE,
    hu.GENERAL: wt.GENERAL_WASTE,
    hu.BULKY: wt.BULKY_WASTE,
}


def _is_calendar_href(href: str) -> bool:
    folded = hu.fold(unquote(href))
    return "hulladeknaptar" in folded or "jaratnaptarak" in folded


def _anchor_label(anchor: Any) -> str:
    text = re.sub(
        r"menetrend pdf letöltés",
        "",
        anchor.get_text(" ", strip=True),
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", text).strip()


def _absolute_url(href: str) -> str:
    joined = urljoin(_BASE_URL + "/", href)
    return quote(unquote(joined), safe=":/?#[]@!$&'()*+,;=")


def _calendars(html: str) -> list[tuple[str, str]]:
    """(area label, calendar URL) pairs of the járatterv page.

    The page often splits the download icon and the settlement name into
    sibling anchors of one table row; the PDF href may sit on either one.
    """
    soup = BeautifulSoup(html, "html.parser")
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(label: str, href: str) -> None:
        label = re.sub(r"\s+", " ", label).strip()
        if not label or not href or not _is_calendar_href(href):
            return
        url = _absolute_url(href)
        key = (hu.fold(label), url)
        if key not in seen:
            seen.add(key)
            found.append((label, url))

    for row in soup.select("table tr"):
        hrefs = [
            a.get("href") or ""
            for a in row.find_all("a")
            if _is_calendar_href(a.get("href") or "")
        ]
        if not hrefs:
            continue
        labels = [
            label
            for a in row.find_all("a")
            if (label := _anchor_label(a)) and len(label) <= 80
        ]
        if labels:
            # Prefer the short settlement/district name over any caption.
            label = min(labels, key=len)
        else:
            raw = re.sub(
                r"menetrend pdf letöltés",
                "",
                row.get_text(" ", strip=True),
                flags=re.IGNORECASE,
            )
            label = re.split(r"[;\n]", raw, maxsplit=1)[0].strip()
        href = next(
            (item for item in hrefs if unquote(item).lower().endswith(".pdf")),
            hrefs[0],
        )
        add(label, href)

    if not found:
        for anchor in soup.find_all("a"):
            add(_anchor_label(anchor), anchor.get("href") or "")
    return found


def _pdf_url(response: Any, *_keys: Any, area: str, **_params: Any) -> str:
    """The calendar PDF of the settlement or district named ``area``."""
    options = _calendars(response.text)
    labels = [label for label, _ in options]
    wanted = hu.fold(area)
    exact = [item for item in options if hu.fold(item[0]) == wanted]
    matches = exact or [item for item in options if wanted in hu.fold(item[0])]
    if len(matches) == 1:
        return matches[0][1]
    if matches:
        raise SourceArgAmbiguousWithSuggestions(
            "area", area, [label for label, _ in matches]
        )
    raise SourceArgumentNotFoundWithSuggestions("area", area, labels)


@final
class Source(BaseSource):
    TITLE = "Siókom Nonprofit Kft."
    DESCRIPTION = (
        "Source for Siókom Nonprofit Kft. waste calendars "
        "(Siófok and surrounding settlements, Hungary)."
    )
    URL = "https://www.siokom.hu"
    COUNTRY = "hu"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@tothi"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Balatonvilágos": {"area": "Balatonvilágos"},
        "Ádánd": {"area": "Ádánd"},
        "Siófok Cs-v": {"area": "Siófok Cs-v"},
        "Zamárdi vasúttól délre": {"area": "Zamárdi vasúttól délre"},
        "Kötcse": {"area": "Kötcse"},
        "Enying": {"area": "Enying"},
    }

    PARAMS = (text_field("area", "Settlement / district"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open https://www.siokom.hu/jaratterv/ and copy the settlement or "
            "district name exactly as listed (e.g. 'Balatonvilágos', "
            "'Siófok Cs-v', 'Zamárdi Kőhegy'). Use the short name, not the "
            "neighbourhood description under Siófok rows. There is no street "
            "selector."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_CALENDAR_URL, pick=_pdf_url),),
        url=lambda *keys, **_: keys[-1],
        headers={"Referer": _CALENDAR_URL},
        raise_for_status=True,
        timeout=60,
    )
    parse = hu.CalendarParser(
        types={"szelektív": "szelektív", "zöldhulladék": "zöldhulladék"},
        skip=r"gyűjtés:|gyűjtésbe|gyűjtést|anyagok|például|tájékoztató",
        max_row_length=220,
        bulky=True,
    )
    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)
