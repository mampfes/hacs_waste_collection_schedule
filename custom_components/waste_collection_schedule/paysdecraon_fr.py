import colorsys
import datetime
import logging
import re
import unicodedata
from collections import Counter
from io import BytesIO

import requests
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTCurve
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

_LOGGER = logging.getLogger(__name__)

TITLE = "Communauté de Communes du Pays de Craon"
DESCRIPTION = "Source for the Communauté de Communes du Pays de Craon (Mayenne), France, including Saint-Michel-de-la-Roë."
URL = "https://www.paysdecraon.fr"
COUNTRY = "fr"
TEST_CASES = {
    "Saint-Michel-de-la-Roë (mercredi)": {
        "weekday": "mercredi",
        "commune": "Saint-Michel-de-la-Roë",
    },
    "Craon (lundi)": {"weekday": "lundi", "commune": "Craon"},
    "No commune (friday)": {"weekday": "friday"},
}

EXTRA_INFO = [
    {
        "title": "Saint-Michel-de-la-Roë",
        "url": URL,
        "country": "fr",
        "default_params": {"commune": "Saint-Michel-de-la-Roë"},
    },
]

OM = "Ordures Ménagères"
EMBALLAGES = "Emballages"
BROYAGE = "Broyage de branches"
_HOLIDAY = "Férié"

ICON_MAP = {
    OM: Icons.GENERAL_WASTE,
    EMBALLAGES: Icons.PLASTIC_PACKAGING,
    BROYAGE: Icons.GARDEN,
}

MEDIA_API_URL = "https://www.paysdecraon.fr/wp-json/wp/v2/media"
CALENDAR_PAGE_URL = "https://www.paysdecraon.fr/environnement/dechets-et-dechetteries/"
PDF_NAME_REGEX = re.compile(r"calendrier-collecte-(\d{4})[^/]*\.pdf$", re.IGNORECASE)

WEEKDAYS = {
    "lundi": 0,
    "monday": 0,
    "mardi": 1,
    "tuesday": 1,
    "mercredi": 2,
    "wednesday": 2,
    "jeudi": 3,
    "thursday": 3,
    "vendredi": 4,
    "friday": 4,
}
WEEKDAY_SUGGESTIONS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
# French weekday initials as printed in the calendar (Monday ... Sunday)
WEEKDAY_LETTERS = "LMMJVSD"

PARAM_TRANSLATIONS = {
    "en": {"weekday": "Collection weekday", "commune": "Municipality"},
    "de": {"weekday": "Abholwochentag", "commune": "Gemeinde"},
    "it": {"weekday": "Giorno di raccolta", "commune": "Comune"},
    "fr": {"weekday": "Jour de collecte", "commune": "Commune"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "weekday": "Your usual collection weekday (lundi, mardi, mercredi, jeudi, vendredi or the English names). Collections are automatically shifted by one day after public holidays.",
        "commune": "Optional: your municipality (e.g. Saint-Michel-de-la-Roë), used to add the branch shredding (Broyage de branches) date.",
    },
    "de": {
        "weekday": "Ihr üblicher Abholwochentag (lundi, mardi, mercredi, jeudi, vendredi oder die englischen Namen). Nach Feiertagen werden die Abholungen automatisch um einen Tag verschoben.",
        "commune": "Optional: Ihre Gemeinde (z.B. Saint-Michel-de-la-Roë), um den Termin für das Häckseln von Ästen (Broyage de branches) hinzuzufügen.",
    },
    "it": {
        "weekday": "Il tuo giorno di raccolta abituale (lundi, mardi, mercredi, jeudi, vendredi o i nomi inglesi). Dopo un giorno festivo la raccolta viene spostata automaticamente di un giorno.",
        "commune": "Facoltativo: il tuo comune (es. Saint-Michel-de-la-Roë), per aggiungere la data di triturazione dei rami (Broyage de branches).",
    },
    "fr": {
        "weekday": "Votre jour de collecte habituel (lundi, mardi, mercredi, jeudi ou vendredi). Après un jour férié, la collecte est automatiquement décalée au lendemain.",
        "commune": "Facultatif : votre commune (ex. Saint-Michel-de-la-Roë), pour ajouter la date de broyage de branches.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "The Pays de Craon calendar (https://www.paysdecraon.fr/environnement/dechets-et-dechetteries/) only shows whether a week is a household waste or a packaging week. Enter the weekday on which your bins are usually collected. Optionally enter your municipality to also get the branch shredding date.",
    "fr": "Le calendrier du Pays de Craon (https://www.paysdecraon.fr/environnement/dechets-et-dechetteries/) indique uniquement si une semaine est une semaine Ordures Ménagères ou Emballages. Indiquez le jour de la semaine où vos bacs sont habituellement collectés. Indiquez éventuellement votre commune pour obtenir aussi la date de broyage de branches.",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"\bsaint\b", "st", text)
    text = re.sub(r"\bsainte\b", "ste", text)
    return re.sub(r"[^a-z0-9]", "", text)


def _to_rgb(color) -> tuple[float, float, float] | None:
    if color is None:
        return None
    if isinstance(color, (int, float)):
        color = (color,)
    try:
        values = [float(v) for v in color]
    except (TypeError, ValueError):
        return None
    if len(values) == 1:
        return (values[0], values[0], values[0])
    if len(values) == 3:
        return (values[0], values[1], values[2])
    if len(values) == 4:
        c, m, y, k = values
        return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
    return None


def _classify_color(color) -> str | None:
    """Map a cell background colour to its meaning (see legend of the PDF)."""
    rgb = _to_rgb(color)
    if rgb is None:
        return None
    hue, saturation, value = colorsys.rgb_to_hsv(*rgb)
    if saturation < 0.4 or value < 0.3:
        return None
    if hue >= 0.83 or hue < 0.04:
        return OM  # bordeaux / magenta
    if 0.05 <= hue < 0.19:
        return EMBALLAGES  # yellow / orange
    if 0.19 <= hue < 0.47:
        return _HOLIDAY  # green
    if 0.52 <= hue < 0.75:
        return BROYAGE  # blue
    return None


def _walk(obj, chars: list, shapes: list) -> None:
    if isinstance(obj, LTChar):
        chars.append(obj)
        return
    if isinstance(obj, LTCurve):
        if obj.fill:
            shapes.append(obj)
        return
    if hasattr(obj, "__iter__"):
        for child in obj:
            _walk(child, chars, shapes)


def _chars_to_text(chars: list) -> str:
    text = ""
    last = None
    for c in sorted(chars, key=lambda c: c.x0):
        if last is not None and c.x0 - last.x1 > 0.3 * max(c.width, 1):
            text += " "
        text += c.get_text()
        last = c
    return text.strip()


def _parse_pdf(content: bytes, year: int) -> tuple[dict, dict]:
    """Parse a 'calendrier de collecte' PDF.

    The PDF shows 14 month columns (January of `year` to February of the next
    year). Every day is a row, coloured according to the type of collection
    taking place that week.

    Returns a dict date -> category and a dict date -> list of communes
    (branch shredding).
    """
    cells = []  # (page_no, x0, day, letter, category, extra_text)
    for page_no, page in enumerate(extract_pages(BytesIO(content))):
        chars: list = []
        shapes: list = []
        _walk(page, chars, shapes)

        for shape in shapes:
            width, height = shape.width, shape.height
            if not (25 < width < 130 and 6 < height < 18 and width > 3 * height):
                continue
            category = _classify_color(shape.non_stroking_color)
            if category is None:
                continue

            inside = [
                c
                for c in chars
                if shape.x0 <= (c.x0 + c.x1) / 2 <= shape.x1
                and shape.y0 <= (c.y0 + c.y1) / 2 <= shape.y1
                and c.get_text().strip()
            ]
            inside.sort(key=lambda c: c.x0)

            # day number = first group of adjacent digits
            day_chars: list = []
            for c in inside:
                if c.get_text().isdigit():
                    if day_chars and c.x0 - day_chars[-1].x1 > max(c.width, 1):
                        break
                    day_chars.append(c)
                elif day_chars:
                    break
            if not day_chars:
                continue  # legend box or similar

            letters = [
                c
                for c in inside
                if c.x1 <= day_chars[0].x0 + 0.5 and c.get_text().isalpha()
            ]
            letter = letters[-1].get_text().upper() if letters else ""
            if any(c.get_text() == "*" for c in inside):
                category = _HOLIDAY

            rest = [
                c
                for c in inside
                if c.x0 > day_chars[-1].x1 - 0.5 and c.get_text() != "*"
            ]
            extra = re.sub(r"\bS\.\s?\d+\b", "", _chars_to_text(rest)).strip()
            cells.append(
                (
                    page_no,
                    shape.x0,
                    int("".join(c.get_text() for c in day_chars)),
                    letter,
                    category,
                    extra,
                )
            )

    if not cells:
        raise ValueError("No calendar cells found in PDF")

    # group cells into month columns (in reading order: page, then x position)
    columns: list[list[tuple]] = []
    for cell in sorted(cells, key=lambda c: (c[0], c[1])):
        if (
            columns
            and columns[-1][0][0] == cell[0]
            and abs(columns[-1][0][1] - cell[1]) < 10
        ):
            columns[-1].append(cell)
        else:
            columns.append([cell])

    categories: dict[datetime.date, str] = {}
    shredding: dict[datetime.date, list[str]] = {}
    for index, column in enumerate(columns):
        col_year = year + index // 12
        col_month = index % 12 + 1
        for _, _, day, letter, category, extra in column:
            try:
                date = datetime.date(col_year, col_month, day)
            except ValueError as e:
                raise ValueError(
                    f"Unexpected PDF layout: invalid date {col_year}-{col_month}-{day}"
                ) from e
            if letter and letter != WEEKDAY_LETTERS[date.weekday()]:
                raise ValueError(
                    f"Unexpected PDF layout: weekday mismatch for {date.isoformat()}"
                )
            categories[date] = category
            if category == BROYAGE and extra:
                shredding.setdefault(date, []).append(extra)

    return categories, shredding


class Source:
    def __init__(self, weekday: str, commune: str | None = None):
        key = _normalize(str(weekday))
        if key not in WEEKDAYS:
            raise SourceArgumentNotFoundWithSuggestions(
                "weekday", weekday, WEEKDAY_SUGGESTIONS
            )
        self._weekday = WEEKDAYS[key]
        self._commune = _normalize(commune) if commune else None

    def _get_pdf_urls(self) -> dict[int, str]:
        r = requests.get(
            MEDIA_API_URL,
            params={
                "search": "calendrier-collecte",
                "per_page": 50,
                "_fields": "date,source_url",
            },
            timeout=30,
        )
        r.raise_for_status()

        latest: dict[int, tuple[str, str]] = {}
        for item in r.json():
            url = item.get("source_url") or ""
            match = PDF_NAME_REGEX.search(url)
            if not match:
                continue
            year = int(match.group(1))
            date = item.get("date") or ""
            if year not in latest or date > latest[year][0]:
                latest[year] = (date, url)

        if not latest:
            raise ValueError(
                f"No collection calendar PDF found, please check {CALENDAR_PAGE_URL}"
            )

        this_year = datetime.date.today().year
        years = [y for y in latest if y >= this_year] or [max(latest)]
        return {y: latest[y][1] for y in sorted(years)}

    def fetch(self) -> list[Collection]:
        categories: dict[datetime.date, str] = {}
        shredding: dict[datetime.date, list[str]] = {}
        errors: list[Exception] = []

        # newer calendars override older ones for overlapping dates
        for year, url in self._get_pdf_urls().items():
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            try:
                cats, shreds = _parse_pdf(r.content, year)
            except ValueError as e:
                _LOGGER.warning("Could not parse calendar %s: %s", url, e)
                errors.append(e)
                continue
            categories.update(cats)
            shredding.update(shreds)

        if not categories:
            raise errors[0] if errors else ValueError("No collection dates found")

        # group days by week: the calendar colours whole weeks
        weeks: dict[datetime.date, set[int]] = {}
        for date, category in categories.items():
            monday = date - datetime.timedelta(days=date.weekday())
            holidays = weeks.setdefault(monday, set())
            if category == _HOLIDAY:
                holidays.add(date.weekday())

        entries = []
        for monday, holidays in weeks.items():
            # after a public holiday the collection is postponed by one day
            shift = 1 if any(h <= self._weekday for h in holidays) else 0
            date = monday + datetime.timedelta(days=self._weekday + shift)
            category = categories.get(date)
            if category == BROYAGE:
                # branch shredding day: use the type of the rest of the week
                week = Counter(
                    categories.get(monday + datetime.timedelta(days=i))
                    for i in range(6)
                )
                category = next(
                    (c for c, _ in week.most_common() if c in (OM, EMBALLAGES)),
                    None,
                )
            if category in (OM, EMBALLAGES):
                entries.append(Collection(date, category, ICON_MAP[category]))

        if self._commune:
            for date, communes in shredding.items():
                if any(_normalize(c) == self._commune for c in communes):
                    entries.append(Collection(date, BROYAGE, ICON_MAP[BROYAGE]))

        return entries
