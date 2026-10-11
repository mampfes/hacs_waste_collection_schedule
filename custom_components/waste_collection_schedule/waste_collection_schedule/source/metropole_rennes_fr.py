"""Waste collection schedules for Rennes Métropole, France.

The metropole publishes one calendar per town (or group of towns, or quarter of
Rennes) as a PDF, most often behind a Heyzine flip-book viewer. Each calendar
is a grid of months side by side with one row per day; the collection days are
the rows highlighted in grey (household waste) or yellow (recyclables). The
calendar index page lists the current edition and, while a new one is about to
take effect, the previous one, which bridges the gap.

``PdfWordLayoutParser`` exposes the positioned day numbers, month headings and
filled rectangles; ``_calendar_rows`` pairs a highlighted row with the day number
printed on its left and the month heading above its column.
"""

import re
import unicodedata
from collections.abc import Iterable
from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import Compose, Deduplicate, SortRows
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://dechets.metropole.rennes.fr"
_CALENDAR_PAGE_URL = f"{_URL}/ou-et-comment-jeter-vos-dechets/"

_HEYZINE_LINK = re.compile(r"^https://heyzine\.com/flip-book/[^/]+\.html")
_HEYZINE_PDF = re.compile(r"https://cdnm\.heyzine\.com/[^\"'\s\\<>]+\.pdf")
_PDF_LINK = re.compile(r"\.pdf(\?|$)", re.IGNORECASE)

_MONTHS = {
    "JANVIER": 1,
    "FEVRIER": 2,
    "MARS": 3,
    "AVRIL": 4,
    "MAI": 5,
    "JUIN": 6,
    "JUILLET": 7,
    "AOUT": 8,
    "SEPTEMBRE": 9,
    "OCTOBRE": 10,
    "NOVEMBRE": 11,
    "DECEMBRE": 12,
}
_MONTH_HEADER = re.compile(r"^(" + "|".join(_MONTHS) + r")(?:\s+(\d{4}))?$")
_SEASON = re.compile(r"(20\d{2})\s*/\s*(20\d{2})")
_DAY_NUMBER = re.compile(r"^([1-9]|[12][0-9]|3[01])$")

# Background colours used for the highlighted collection rows of the calendar grid.
_MARKER_COLORS: tuple[tuple[tuple[float, float, float], str], ...] = (
    ((0.745, 0.735, 0.741), "Ordures ménagères"),
    ((1.0, 0.8, 0.0), "Déchets recyclables"),
)
_COLOR_TOLERANCE = 0.06
# Day numbers are printed just left of the highlighted row.
_DAY_SEARCH_WIDTH = 60

_TYPE_MAP = {
    "Ordures ménagères": wt.GENERAL_WASTE,
    "Déchets recyclables": wt.RECYCLABLES,
}

_RENNES_QUARTERS = (
    "Q2 - Thabor - Saint-Hélier - Alphonse Guérin - Baud-Chardonnet",
    "Q3 - Bourg-l'Évesque - la Touche - Moulin du Comte",
    "Q4 - Saint-Martin",
    "Q5 - Maurepas - La Bellangerais",
    "Q6 - Jeanne d'Arc - Longs-Champs - Beaulieu",
    "Q7 - La Pommeraie",
    "Q8 - Sud-Gare",
    "Q9 - Cleunay - Arsenal-Redon - La Courrouze",
    "Q10 - Villejean - Beauregard",
    "Q11 - Le Blosne",
    "Q12 - Bréquigny",
)

_COMMUNES = (
    "Acigné",
    "Bécherel",
    "Betton",
    "Bourgbarré",
    "Brécé",
    "Bruz",
    "Cesson-Sévigné",
    "Chantepie",
    "Chartres-de-Bretagne",
    "Chavagne",
    "Chevaigné",
    "Cintré",
    "Clayes",
    "Corps-Nuds",
    "Gévezé",
    "L'Hermitage",
    "La Chapelle-Chaussée",
    "La Chapelle-des-Fougeretz",
    "La Chapelle-Thouarault",
    "Laillé",
    "Langan",
    "Le Rheu",
    "Le Verger",
    "Miniac-sous-Bécherel",
    "Montgermont",
    "Mordelles",
    "Nouvoitou",
    "Noyal-Châtillon-sur-Seiche",
    "Orgères",
    "Pacé",
    "Parthenay-de-Bretagne",
    "Pont-Péan",
    "Romillé",
    "Saint-Armel",
    "Saint-Erblon",
    "Saint-Gilles",
    "Saint-Grégoire",
    "Saint-Jacques-de-la-Lande",
    "Saint-Sulpice-la-Forêt",
    "Thorigné-Fouillard",
    "Vern-sur-Seiche",
    "Vezin-le-Coquet",
)


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def _normalize(value: str) -> str:
    """Lower-case, de-accent and collapse whitespace of a label."""
    value = value.replace("’", "'").replace("–", "-").replace("—", "-")
    return " ".join(_strip_accents(value).lower().split())


def _tokens(label: str) -> set[str]:
    """Split a calendar label into its individual town / quarter names."""
    parts = re.split(r"\s+-\s+|,", _normalize(label))
    return {re.sub(r"[^a-z0-9]", "", part) for part in parts if part.strip()}


def _calendar_links(html: str) -> list[tuple[str, str, bool]]:
    """Return every calendar of the index page as (label, url, is_current)."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[tuple[str, str, bool]] = []
    for heading in soup.select("h2, h3"):
        title = heading.get_text(" ", strip=True)
        if "calendrier" not in _normalize(title):
            continue
        block = heading.find_parent(class_="block")
        if not isinstance(block, Tag):
            continue
        # Older editions stay online until the new one takes effect.
        current = "valable" not in _normalize(title)
        for anchor in block.find_all("a", href=True):
            href = str(anchor["href"])
            if (
                not _HEYZINE_LINK.match(href)
                and not _PDF_LINK.search(href)
                and "osuny.org/media/download" not in href
            ):
                continue
            label = anchor.get_text(" ", strip=True)
            label = re.sub(r"\(?\s*lien externe\s*\)?", "", label)
            label = label.strip(" ,-–")
            if label:
                links.append((label, href, current))
    return links


def _match(links: list[tuple[str, str, bool]], commune: str) -> tuple[str, str, bool]:
    candidates = [link for link in links if link[2]] or links
    wanted = _normalize(commune)
    wanted_tokens = _tokens(commune)

    for link in candidates:
        if _normalize(link[0]) == wanted:
            return link
    for link in candidates:
        if wanted_tokens and wanted_tokens <= _tokens(link[0]):
            return link
    raise SourceArgumentNotFoundWithSuggestions(
        "commune", commune, sorted(link[0] for link in candidates)
    )


def _calendar_urls(response, *_, commune: str, **__) -> list[str]:
    """Lookup pick: the calendar of the commune, then its previous edition."""
    links = _calendar_links(response.text)
    current = _match(links, commune)
    urls = [current[1]]
    # While the new edition is already published but not yet in effect, the
    # previous one bridges the gap.
    current_tokens = _tokens(current[0])
    for label, url, is_current in links:
        if not is_current and _tokens(label) & current_tokens and url not in urls:
            urls.append(url)
            break
    return urls


def _direct_url(url: str, *_, **__) -> str | None:
    """Lookup ``given``: a PDF link needs no resolving, only a flip-book does."""
    return None if _HEYZINE_LINK.match(url) else url


def _flipbook_pdf(response, url: str, *_, **__) -> str:
    """Lookup pick: the PDF behind a Heyzine flip-book viewer page."""
    matches = _HEYZINE_PDF.findall(response.text.replace("\\/", "/"))
    response_shape.expect(
        bool(matches),
        source_name="Rennes Métropole",
        detail=f"could not find the calendar PDF behind {url}",
        raw=response.text[:500],
    )
    return matches[0]


def _classify_color(color: tuple[float, ...] | None) -> str | None:
    if not color or len(color) != 3:
        return None
    for reference, waste_type in _MARKER_COLORS:
        if all(
            abs(value - expected) <= _COLOR_TOLERANCE
            for value, expected in zip(color, reference, strict=False)
        ):
            return waste_type
    return None


def _season(layout: parsers.PdfWordLayout) -> re.Match | None:
    # The season is printed once in a heading, e.g. "Vos collectes de déchets
    # 2026/2027"; it may be split into several words.
    for text in (
        " ".join(line.text for line in layout.lines),
        "".join(word.text for word in layout.words),
    ):
        if match := _SEASON.search(text):
            return match
    return None


def _calendar_rows(
    layouts: list[parsers.PdfWordLayout], source: BaseSource | None = None
) -> Iterable[tuple[date, str]]:
    """Pair every highlighted row with its printed day number and month heading."""
    for layout in layouts:
        season = _season(layout)
        months: list[tuple[int, int, int | None, float, float]] = []
        days: list[tuple[int, float, float, int]] = []
        for line in layout.lines:
            text = " ".join(line.text.split())
            if header := _MONTH_HEADER.match(_strip_accents(text).upper()):
                months.append(
                    (
                        line.page,
                        _MONTHS[header.group(1)],
                        int(header.group(2)) if header.group(2) else None,
                        line.x,
                        line.y,
                    )
                )
            elif _DAY_NUMBER.match(text):
                days.append((line.page, line.x, line.y, int(text)))

        found = 0
        for vector in layout.vectors:
            waste_type = _classify_color(vector.fill_color)
            height = vector.y1 - vector.y0
            if waste_type is None or not 8 < height < 20 or vector.x1 - vector.x0 < 30:
                continue
            # The day number sits on the same row, just left of the highlighted cell.
            numbers = sorted(
                (abs(vector.x0 - x), day, x)
                for page, x, y, day in days
                if page == vector.page
                and vector.y0 + 2 < y < vector.y1 - 2
                and x <= vector.x0 + 2
                and x > vector.x0 - _DAY_SEARCH_WIDTH
            )
            if not numbers:
                continue
            # The month is the heading of the column the highlighted cell is in.
            centre = (vector.x0 + vector.x1) / 2
            headings = sorted(
                (abs(x - centre), month, year)
                for page, month, year, x, y in months
                if page == vector.page and y >= vector.y0
            )
            if not headings:
                continue
            _, month, year = headings[0]
            if year is None:
                if season is None:
                    continue
                # Calendars run from October of the first year to September of
                # the second one.
                year = int(season.group(1) if month >= 10 else season.group(2))
            try:
                row = date(year, month, numbers[0][1])
            except ValueError:
                continue
            found += 1
            yield row, waste_type

        response_shape.expect(
            found > 0,
            source_name=response_shape.source_name(source),
            detail="no highlighted collection rows found in the calendar PDF",
            raw=str(layout.lines[:10]),
        )


@final
class Source(BaseSource):
    TITLE = "Rennes Métropole"
    DESCRIPTION = "Source for Rennes Métropole, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@Plarkass"]

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Cesson-Sévigné": {"commune": "Cesson-Sévigné"},
        "Chantepie": {"commune": "Chantepie"},
        "Rennes Q2": {
            "commune": "Q2 - Thabor - Saint-Hélier - Alphonse Guérin - Baud-Chardonnet"
        },
        "Le Rheu (grouped calendar)": {"commune": "Le Rheu"},
    }

    PARAMS = (municipality("commune"),)

    REGIONS = (
        *(
            region(f"Rennes {quarter}", commune=quarter)
            for quarter in sorted(
                _RENNES_QUARTERS, key=lambda q: int(q.split(" ")[0][1:])
            )
        ),
        *(region(commune, commune=commune) for commune in _COMMUNES),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/ "
            "and look at the lists of collection calendars. Use the name of the entry "
            "covering your address as `commune`, for example `Cesson-Sévigné`. If "
            "several towns share one calendar (for example `Bruz - Chavagne`), the "
            "name of your own town is enough. Inside the city of Rennes, use the "
            "quarter, for example `Q7 - La Pommeraie` or just `Q7`."
        ),
        "fr": (
            "Ouvrez https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/ "
            "et consultez les listes des calendriers de collecte. Utilisez le nom de "
            "l'entrée qui couvre votre adresse comme `commune`, par exemple "
            "`Cesson-Sévigné`. Si plusieurs communes partagent un calendrier (par "
            "exemple `Bruz - Chavagne`), le nom de votre commune suffit. Dans "
            "Rennes, utilisez le quartier, par exemple `Q7 - La Pommeraie` ou "
            "simplement `Q7`."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_CALENDAR_PAGE_URL, pick=_calendar_urls),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(
            lambda target, context, pdf_url, **_: pdf_url,
            before=(
                retrievers.Lookup(
                    lambda target, *_, **__: target,
                    given=_direct_url,
                    pick=_flipbook_pdf,
                ),
            ),
            timeout=60,
        ),
    )
    parse = parsers.EachResponse(
        parsers.PdfWordLayoutParser(min_words=50, min_vectors=50),
        then=_calendar_rows,
    )
    preprocess = Compose(Deduplicate(), SortRows())
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
