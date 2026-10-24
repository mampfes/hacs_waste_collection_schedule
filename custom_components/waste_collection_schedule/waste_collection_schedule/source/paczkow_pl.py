"""Gmina Paczków, Poland.

The municipality publishes its collection schedule one quarter at a time, as
two PDFs linked from one page: the town ("kwartal-iv-2026-paczkow.pdf") and
the villages ("kwartal-iv-2026-solectwa.pdf"). The source keeps the newest
quarter's files (and any later one already posted) and reads both.

Each PDF is a run of small tables, one per area: the area (the town's streets
after "Ulice:", or a list of villages), a header row naming the quarter's three
months ("PAŹDZIERNIK 2026 LISTOPAD 2026 GRUDZIEŃ 2026"), then one row per waste
round listing its days per month ("06, 20 03, 17 01, 15, 29": a month's days
are comma-joined, months are separated by a space). Tables are grouped under a
"Budynki jednorodzinne" / "Budynki wielorodzinne" heading, since detached and
multi-family houses are collected on different days. The town PDF closes with
a table for non-residential properties, which is not read.
"""

import datetime
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import lookups, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = (
    "https://paczkow.pl/2442/"
    "harmonogram-odbioru-odpadow-komunalnych-na-terenie-gminy-paczkow.html"
)
_LINK_PATTERN = re.compile(
    r"/kwartal-(i{1,3}|iv)-(20\d\d)-(?:paczkow|solectwa)[^/]*\.pdf", re.I
)
_QUARTERS = {"i": 1, "ii": 2, "iii": 3, "iv": 4}

_HEADER = re.compile(
    r"RODZAJ ODEBRANEGO ODPADU\s+((?:[A-ZĄĆĘŁŃÓŚŹŻ]+\s+20\d\d\s*){1,3})", re.I
)
_MONTH_YEAR = re.compile(r"([A-ZĄĆĘŁŃÓŚŹŻ]+)\s+(20\d\d)", re.I)
# One month's days: "06" or "01, 15, 29".
_DAY_GROUP = re.compile(r"\d{1,2}(?:\s*,\s*\d{1,2})*")
_NON_RESIDENTIAL = re.compile(r"Nieruchomości\s+nie\s*zamieszkałe", re.I)
_FOOTER = re.compile(r"nie mają prawa wchodzenia na teren posesji\)?", re.I)

_TYPES = {
    "Zmieszane odpady komunalne": wt.GENERAL_WASTE,
    "Wyselekcjonowane odpady z tworzyw sztucznych": wt.RECYCLABLES,
    "Wyselekcjonowane odpady papierowe": wt.PAPER,
    "Odpady BIO": wt.ORGANIC,
}


def _quarter_pdfs(response: Any, **_: Any) -> list[str]:
    """The newest quarter's PDFs, plus any later quarter already linked."""
    links: dict[str, tuple[int, int]] = {}
    for href in re.findall(r'href="([^"]+)"', response.text):
        match = _LINK_PATTERN.search(href)
        if match:
            url = retrievers.urljoin(response.url, href.replace("&amp;", "&"))
            links.setdefault(
                url, (int(match.group(2)), _QUARTERS[match.group(1).lower()])
            )
    if not links:
        raise ValueError("Paczków: no quarterly schedule PDF linked")
    today = datetime.date.today()
    current = (today.year, (today.month - 1) // 3 + 1)
    wanted = [url for url, quarter in links.items() if quarter >= current]
    if not wanted:
        newest = max(links.values())
        wanted = [url for url, quarter in links.items() if quarter == newest]
    return wanted


def _tables(text: str, _source: Any = None) -> list[dict[str, Any]]:
    """Split one PDF's text into its area tables (residential only)."""
    # The town PDF ends with the non-residential properties' table (offices,
    # shops, schools), laid out differently: streets inside the rows.
    text = _NON_RESIDENTIAL.split(text)[0]
    tables: list[dict[str, Any]] = []
    multi_family = False
    position = 0
    for header in _HEADER.finditer(text):
        area_text = text[position : header.start()]
        heading = re.findall(r"Budynki\s+(jedno|wielo)rodzinne", area_text, re.I)
        if heading:
            multi_family = heading[-1].lower() == "wielo"
            area_text = re.split(r"Budynki\s+\w+rodzinne", area_text, flags=re.I)[-1]
        area_text = re.sub(r"^\s*Ulice:\s*", "", area_text.strip(), flags=re.I)
        areas = [
            re.sub(r"\s+", " ", name).strip(" .-")
            for name in re.split(r"[;,]", area_text.replace("-\n", "-"))
        ]
        months = [
            (int(year), recurrence.month(name))
            for name, year in _MONTH_YEAR.findall(header.group(1))
        ]
        footer = _FOOTER.search(text, header.end())
        end = footer.end() if footer else len(text)
        rows: list[tuple[datetime.date, str]] = []
        for line in text[header.end() : end].splitlines():
            label = next((key for key in _TYPES if key.lower() in line.lower()), None)
            if label is None:
                continue
            tail = line[line.lower().index(label.lower()) + len(label) :]
            tail = re.sub(r"^[^\d]*", "", tail)
            # A short row would shift days into the wrong month: fail loudly.
            groups = _DAY_GROUP.findall(tail)
            for (year, month), group in zip(months, groups, strict=True):
                for day in re.findall(r"\d+", group):
                    rows.append((datetime.date(year, month, int(day)), label))
        tables.append(
            {
                "areas": [name for name in areas if name],
                "multi_family": multi_family,
                "rows": rows,
            }
        )
        position = end
    return tables


def _select(
    tables: list[dict[str, Any]], source: Any = None
) -> list[tuple[datetime.date, str]]:
    """The rows of the tables naming the configured street or village."""
    wanted = lookups.normalize_loose(source.params["street"])
    multi_family = bool(source.params.get("multi_family", False))
    rows: list[tuple[datetime.date, str]] = []
    names: set[str] = set()
    for table in tables:
        if table["multi_family"] != multi_family:
            continue
        names.update(table["areas"])
        if any(lookups.normalize_loose(name) == wanted for name in table["areas"]):
            rows.extend(table["rows"])
    if not rows:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", source.params["street"], sorted(names)
        )
    return rows


@final
class Source(BaseSource):
    TITLE = "Gmina Paczków"
    DESCRIPTION = "Source for Gmina Paczków, Poland."
    URL = "https://paczkow.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kopernika": {"street": "Kopernika"},
        "Armii Krajowej multi-family": {
            "street": "Armii Krajowej",
            "multi_family": True,
        },
        "Kamienica": {"street": "Kamienica"},
    }

    PARAMS = (
        street("street"),
        boolean("multi_family", default=False),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street (in the town of Paczków) or your village, as "
            "printed in the quarterly schedule PDFs on "
            "https://paczkow.pl/2442/harmonogram-odbioru-odpadow-komunalnych-"
            "na-terenie-gminy-paczkow.html (e.g. 'Kopernika', 'Armii Krajowej' "
            "or 'Kamienica'). Accents and case are ignored. Tick "
            "'multi_family' for a multi-family building (budynek "
            "wielorodzinny)."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_INDEX_URL, pick=_quarter_pdfs),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(parsers.PdfTextParser(min_chars=500), then=_tables)
    preprocess = staticmethod(_select)
    transform = ICSTransformer(type_value_map=_TYPES)
