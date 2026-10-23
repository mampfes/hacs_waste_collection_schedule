"""Calendarize calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

import re
import unicodedata
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

CALENDAR_URL = "https://environnement.clissonsevremaine.fr/dechets/collecte-des-dechets/calendrier-des-collectes"
CATEGORY_ARG = "tx_calendarize_calendar[customSearch][category]"
MONTH_ARG = "tx_calendarize_calendar[month]"
YEAR_ARG = "tx_calendarize_calendar[year]"
MONTHS_TO_FETCH = 12
COMMUNES = [
    "Aigrefeuille-sur-Maine",
    "Boussay",
    "Château-Thébaud",
    "Clisson",
    "Clisson, rue Saint-Antoine",
    "Gétigné - zone A",
    "Gétigné - zone B",
    "Gorges",
    "Haute-Goulaine",
    "La Haye-Fouassière - Zone A",
    "La Haye-Fouassière - Zone B",
    "La Planche",
    "Maisdon-sur-Sèvre - zone 1",
    "Maisdon-sur-Sèvre - zone 2",
    "Maisdon-sur-Sèvre - zone 3",
    "Monnières",
    "Remouillé",
    "Saint-Hilaire-de-Clisson - Zone A",
    "Saint-Hilaire-de-Clisson - Zone B",
    "Saint-Lumine-de-Clisson - Zone A",
    "Saint-Lumine-de-Clisson - Zone B",
    "St-Fiacre-sur-Maine",
    "Vieillevigne",
]
FRENCH_MONTHS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]
COLLECTION_PREFIX = re.compile("^collecte\\s+(?:des?|du|de\\s+la|de\\s+l')\\s+", re.I)


def _normalize(value: str) -> str:
    """Lowercase, strip accents and reduce punctuation to single spaces."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub("[^a-z0-9]+", " ", without_accents.lower()).strip()


def _get_categories(source: BaseSource, session: Any) -> dict[str, str]:
    """Map every municipality label of the drop-down to its category id."""
    r = session.get(CALENDAR_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    select = soup.find("select", attrs={"name": CATEGORY_ARG})
    if select is None:
        raise RuntimeError("Could not find the municipality selector on the page")
    return {
        option.get_text(strip=True): value
        for option in select.find_all("option")
        if isinstance((value := option.get("value")), str) and value
    }


def _parse_month(source: BaseSource, raw):
    r, year, month = raw
    soup = BeautifulSoup(r.text, "html.parser")
    header = soup.find(id="month-header")
    expected = _normalize(f"{FRENCH_MONTHS[month - 1]} {year}")
    # Some unpublished months ignore the query and repeat the current month.
    if header is None or expected not in _normalize(header.get_text(" ", strip=True)):
        return []
    # Calendarize's legend connects each colour to the provider's waste label.
    legend: dict[str, str] = {}
    for span in soup.select("#month-legend span[class*=_catheader_text]"):
        span_classes = span.get("class") or []
        if not isinstance(span_classes, list):
            span_classes = [span_classes]
        for css_class in span_classes:
            if css_class.endswith("_catheader_text"):
                label = COLLECTION_PREFIX.sub("", span.get_text(strip=True))
                legend[css_class.removesuffix("_catheader_text")] = (
                    label[:1].upper() + label[1:]
                )
    entries: list[dict[str, Any]] = []
    for day_cell in soup.select("td.day.hasEvents"):
        classes = day_cell.get("class") or []
        if "not-current-month" in classes:
            continue
        day = int(day_cell.get_text(strip=True))
        for css_class in classes:
            if not css_class.endswith("_catheader_bullet"):
                continue
            colour = css_class.removesuffix("_catheader_bullet")
            if colour not in legend:
                continue
            waste_type = legend[colour]
            entries.append({"date": date(year, month, day), "type": waste_type})
    return entries


def _retrieve(source: BaseSource) -> Any:
    session = source.session
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    categories = _get_categories(source, session)
    wanted = _normalize(source.params["commune"])
    category = next(
        (value for label, value in categories.items() if _normalize(label) == wanted),
        None,
    )
    if category is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "commune", source.params["commune"], sorted(categories)
        )
    today = date.today()
    entries: list[tuple[Any, int, int]] = []
    for offset in range(MONTHS_TO_FETCH):
        month_index = today.month - 1 + offset
        year, month = (today.year + month_index // 12, month_index % 12 + 1)
        r = session.get(
            CALENDAR_URL,
            params={CATEGORY_ARG: category, YEAR_ARG: year, MONTH_ARG: month},
            timeout=30,
        )
        r.raise_for_status()
        entries.append((r, year, month))
    return entries


def _parse(source: BaseSource, raw) -> list[dict[str, Any]]:
    entries = [entry for month in raw for entry in _parse_month(source, month)]
    if not entries:
        raise RuntimeError(
            f"No collection found for {source.params['commune']}, the website layout may have changed"
        )
    return entries


class CalendarRetriever(RetrieverFunc):
    """Retrieve the calendar and context needed to interpret it."""

    def __call__(self, source: BaseSource) -> Any:
        return _retrieve(source)


class CalendarParser(Parser[list[dict[str, Any]]]):
    """Read provider records without classifying their waste types."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        return _parse(source, response)
