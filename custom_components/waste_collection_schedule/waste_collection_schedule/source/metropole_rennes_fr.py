"""Source for Rennes Métropole, France."""

import logging
import re
import unicodedata
from collections.abc import Iterator
from datetime import date, datetime
from io import BytesIO
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTContainer, LTPage, LTRect, LTTextLineHorizontal
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Rennes Métropole"
DESCRIPTION = "Source for Rennes Métropole, France."
URL = "https://dechets.metropole.rennes.fr"
COUNTRY = "fr"

TEST_CASES = {
    "Cesson-Sévigné": {"commune": "Cesson-Sévigné"},
    "Chantepie": {"commune": "Chantepie"},
    "Rennes Q2": {
        "commune": "Q2 - Thabor - Saint-Hélier - Alphonse Guérin - Baud-Chardonnet"
    },
    "Le Rheu (grouped calendar)": {"commune": "Le Rheu"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/ and "
        "look at the lists of collection calendars. Use the name of the entry covering "
        "your address as `commune`, for example `Cesson-Sévigné`. If several towns share "
        "one calendar (for example `Bruz - Chavagne`), the name of your own town is "
        "enough. Inside the city of Rennes, use the quarter, for example `Q7 - La "
        "Pommeraie` or just `Q7`."
    ),
    "fr": (
        "Ouvrez https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/ et "
        "consultez les listes des calendriers de collecte. Utilisez le nom de l'entrée "
        "qui couvre votre adresse comme `commune`, par exemple `Cesson-Sévigné`. Si "
        "plusieurs communes partagent un calendrier (par exemple `Bruz - Chavagne`), le "
        "nom de votre commune suffit. Dans Rennes, utilisez le quartier, par exemple "
        "`Q7 - La Pommeraie` ou simplement `Q7`."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {"commune": "Town or Rennes quarter"},
    "fr": {"commune": "Commune ou quartier de Rennes"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "commune": "Name of the town (or Rennes quarter) as listed on the Rennes Métropole collection calendar page."
    },
    "fr": {
        "commune": "Nom de la commune (ou du quartier de Rennes) tel qu'il apparaît sur la page des calendriers de collecte de Rennes Métropole."
    },
}

SOURCE_CODEOWNERS = ["@Plarkass"]

ICON_MAP = {
    "Ordures ménagères": Icons.GENERAL_WASTE,
    "Déchets recyclables": Icons.RECYCLING,
}

_RENNES_QUARTERS = {
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
}

_COMMUNES = [
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
]

EXTRA_INFO = [
    {
        "title": f"Rennes {quarter}",
        "url": URL,
        "country": COUNTRY,
        "default_params": {"commune": quarter},
    }
    for quarter in sorted(_RENNES_QUARTERS, key=lambda q: int(q.split(" ")[0][1:]))
] + [
    {
        "title": commune,
        "url": URL,
        "country": COUNTRY,
        "default_params": {"commune": commune},
    }
    for commune in _COMMUNES
]

_LOGGER = logging.getLogger(__name__)

CALENDAR_PAGE_URL = (
    "https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

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


def _tokens(label: str) -> set:
    """Split a calendar label into its individual town / quarter names."""
    parts = re.split(r"\s+-\s+|,", _normalize(label))
    return {re.sub(r"[^a-z0-9]", "", part) for part in parts if part.strip()}


class _CalendarLink:
    def __init__(self, label: str, url: str, current: bool) -> None:
        self.label = label
        self.url = url
        self.current = current
        self.tokens = _tokens(label)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"_CalendarLink({self.label!r}, current={self.current})"


def _iter_layout(container: LTContainer) -> Iterator[Any]:
    for element in container:
        yield element
        if isinstance(element, LTContainer) and not isinstance(
            element, LTTextLineHorizontal
        ):
            yield from _iter_layout(element)


def _classify_color(color: Any) -> str | None:
    if not isinstance(color, (tuple, list)) or len(color) != 3:
        return None
    for reference, waste_type in _MARKER_COLORS:
        if all(
            abs(float(value) - expected) <= _COLOR_TOLERANCE
            for value, expected in zip(color, reference, strict=False)
        ):
            return waste_type
    return None


class _PageLayout:
    """One page of a calendar PDF, split into month headers, day numbers and markers."""

    def __init__(self, page: LTPage) -> None:
        self.markers: list[tuple[LTRect, str]] = []
        self.months: list[tuple[int, int | None, float, float]] = []
        self.days: list[tuple[LTTextLineHorizontal, int]] = []
        fragments: list[str] = []

        for element in _iter_layout(page):
            if isinstance(element, LTRect):
                waste_type = _classify_color(element.non_stroking_color)
                if (
                    waste_type is not None
                    and 8 < element.height < 20
                    and element.width >= 30
                ):
                    self.markers.append((element, waste_type))
            elif isinstance(element, LTTextLineHorizontal):
                text = " ".join(element.get_text().split())
                fragments.append(text)
                header = _MONTH_HEADER.match(_strip_accents(text).upper())
                if header:
                    self.months.append(
                        (
                            _MONTHS[header.group(1)],
                            int(header.group(2)) if header.group(2) else None,
                            element.x0,
                            element.x1,
                        )
                    )
                elif _DAY_NUMBER.match(text):
                    self.days.append((element, int(text)))
            elif isinstance(element, LTChar):
                # Some text is drawn inside figures, outside of any text line.
                fragments.append(element.get_text())

        self.season = _SEASON.search("".join(fragments))

    def _month_of(self, rect: LTRect) -> tuple[int, int | None] | None:
        """Return the month column the marker belongs to."""
        best: tuple[float, int, int | None] | None = None
        for month, year, x0, x1 in self.months:
            # Distance between the month header and the marker, 0 if they overlap.
            gap = max(x0 - rect.x1, rect.x0 - x1, 0)
            if gap > _DAY_SEARCH_WIDTH:
                continue
            if best is None or gap < best[0]:
                best = (gap, month, year)
        return None if best is None else (best[1], best[2])

    def _day_of(self, rect: LTRect) -> int | None:
        """Return the day number printed left of the marker, on the same row."""
        numbers = sorted(
            (abs(rect.x0 - line.x1), day)
            for line, day in self.days
            if line.y0 < rect.y1 - 2
            and line.y1 > rect.y0 + 2
            and line.x1 <= rect.x0 + 2
            and line.x0 > rect.x0 - _DAY_SEARCH_WIDTH
        )
        return numbers[0][1] if numbers else None

    def collections(self, season: re.Match | None) -> list[tuple[date, str]]:
        entries: list[tuple[date, str]] = []
        for rect, waste_type in self.markers:
            column = self._month_of(rect)
            day = self._day_of(rect)
            if column is None or day is None:
                continue
            month, year = column
            if year is None:
                if season is None:
                    continue
                # Calendars run from October of the first year to September of the
                # second one.
                year = int(season.group(1) if month >= 10 else season.group(2))
            try:
                entries.append((date(year, month, day), waste_type))
            except ValueError:
                continue
        return entries


class Source:
    def __init__(self, commune: str):
        self._commune: str = commune

    def fetch(self) -> list[Collection]:
        links = self._get_calendar_links()
        current = self._match(links, current_only=True)

        entries = self._parse_calendar(current.url)
        if not entries:
            raise SourceArgumentException(
                "commune",
                f"No collection dates could be read from the calendar of {current.label}",
            )

        # Calendars run from October to September. While the new edition is already
        # published but not yet in effect, fall back to the previous edition to bridge
        # the gap until the new one starts.
        today = datetime.now().date()
        if min(entry[0] for entry in entries) > today:
            entries += self._fetch_previous_edition(links, current, today)

        return [
            Collection(date=day, t=waste_type, icon=ICON_MAP.get(waste_type))
            for day, waste_type in sorted(set(entries))
        ]

    def _fetch_previous_edition(
        self, links: list[_CalendarLink], current: _CalendarLink, today: date
    ) -> list[tuple[date, str]]:
        previous = [
            link for link in links if not link.current and link.tokens & current.tokens
        ]
        if not previous:
            return []
        try:
            return [
                entry
                for entry in self._parse_calendar(previous[0].url)
                if entry[0] >= today
            ]
        except Exception as error:  # previous edition is a nicety, never fatal
            _LOGGER.warning(
                "Could not read the previous edition of the calendar (%s): %s",
                previous[0].label,
                error,
            )
            return []

    def _match(self, links: list[_CalendarLink], current_only: bool) -> _CalendarLink:
        candidates = [link for link in links if link.current or not current_only]
        if not candidates:
            # The page only offers calendars of the previous season.
            candidates = links
        wanted = _normalize(self._commune)
        wanted_tokens = _tokens(self._commune)

        for link in candidates:
            if _normalize(link.label) == wanted:
                return link
        for link in candidates:
            if wanted_tokens and wanted_tokens <= link.tokens:
                return link

        raise SourceArgumentNotFoundWithSuggestions(
            "commune",
            self._commune,
            sorted(link.label for link in candidates),
        )

    def _get_calendar_links(self) -> list[_CalendarLink]:
        response = requests.get(CALENDAR_PAGE_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links: list[_CalendarLink] = []
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
                if not _HEYZINE_LINK.match(href) and not _PDF_LINK.search(href):
                    if "osuny.org/media/download" not in href:
                        continue
                label = anchor.get_text(" ", strip=True)
                label = re.sub(r"\(?\s*lien externe\s*\)?", "", label)
                label = label.strip(" ,-–")
                if not label:
                    continue
                links.append(_CalendarLink(label, href, current))
        return links

    def _parse_calendar(self, url: str) -> list[tuple[date, str]]:
        """Download a calendar and read the highlighted collection days from it."""
        if _HEYZINE_LINK.match(url):
            url = self._resolve_flipbook(url)

        response = requests.get(url, headers=HEADERS, timeout=60)
        response.raise_for_status()

        pages = [_PageLayout(page) for page in extract_pages(BytesIO(response.content))]
        # Older editions print the month names without a year, but every page carries
        # the season (for example "2026/2027") somewhere in its layout.
        season = next((page.season for page in pages if page.season), None)

        entries: list[tuple[date, str]] = []
        for page_layout in pages:
            entries += page_layout.collections(season)
        return entries

    def _resolve_flipbook(self, url: str) -> str:
        """Extract the PDF behind a Heyzine flip book viewer page."""
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        matches = _HEYZINE_PDF.findall(response.text.replace("\\/", "/"))
        if not matches:
            raise SourceArgumentException(
                "commune",
                f"Could not find the calendar PDF behind {url}",
            )
        return matches[0]
