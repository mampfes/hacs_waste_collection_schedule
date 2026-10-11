import datetime
import re
from collections.abc import Iterator
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a static page listing every commune of the Métropole with its
# collection weekdays under one heading per stream. ArgumentLookup picks the
# commune's block; _describe() reads each heading's section on its own (household
# waste vs. packaging) and RecurrenceExpander projects each named weekday weekly.
#
# Only communes whose schedule is one fixed set of weekdays for the whole
# commune are offered. Communes with alternating weeks, seasonal periods or
# per-district rounds are not approximated.

COLLECTION_URL = (
    "https://www.nicecotedazur.org/services/dechets/collecte-et-tri-dechets/"
    "jours-et-horaires-de-collecte/"
)

SUPPORTED_COMMUNES = [
    "Aspremont",
    "Beaulieu-sur-Mer",
    "Cap d'Ail",
    "Castagniers",
    "Colomars",
    "Èze",
    "Falicon",
    "La Trinité",
    "Le Broc",
    "Nice",
    "Saint-Blaise",
    "Saint-Jean-Cap-Ferrat",
    "Saint-Laurent-du-Var",
    "Saint-Martin-du-Var",
    "Villefranche-sur-Mer",
]

GENERAL_WASTE = "Ordures ménagères"
RECYCLING = "Emballages ménagers"

_WEEKS_AHEAD = 26

# "(sauf le 1er mai)": a published one-off cancellation of the weekly round.
_EXCEPT_RE = re.compile(r"sauf\s+le\s+(\d{1,2})(?:er)?\s+([^\W\d_]+)", re.IGNORECASE)
_WORD_RE = re.compile(r"[^\W\d_]+")


def _normalise(name: str) -> str:
    """Typographic apostrophe (U+2019) to ASCII: 'Cap d’Ail' -> "Cap d'Ail"."""
    return " ".join(name.replace("\u2019", "'").split())


def _communes(blocks: list[Tag], source) -> dict[str, Tag]:
    """Map each supported commune on the page to its content block."""
    supported = {_normalise(name) for name in SUPPORTED_COMMUNES}
    table: dict[str, Tag] = {}
    for block in blocks:
        title = block.select_one(".entry-title")
        content = block.select_one(".entry-content")
        if title is None or content is None:
            continue
        name = _normalise(title.get_text(" ", strip=True))
        if name in supported:
            table[name] = content
    return table


def _heading(element: Tag) -> str | None:
    """The text of a bold section heading paragraph, else None."""
    if element.name != "p":
        return None
    bold = element.find(["strong", "b"])
    if not isinstance(bold, Tag):
        return None
    text = element.get_text(" ", strip=True)
    if bold.get_text(" ", strip=True).rstrip(" :") != text.rstrip(" :"):
        return None
    return text


def _stream(heading: str) -> str | None:
    """The waste stream a section heading introduces (None: not a kerbside round)."""
    text = heading.lower()
    if "encombrant" in text or "électroménager" in text:
        return None
    if "emballages" in text or "bacs jaunes" in text or "sélective" in text:
        return RECYCLING
    if "ordures ménagères" in text:
        return GENERAL_WASTE
    return None


def _sections(content: Tag) -> Iterator[tuple[str, str]]:
    """Yield (stream, section text) for each household-waste / packaging heading."""
    stream: str | None = None
    texts: list[str] = []
    for element in content.find_all(recursive=False):
        heading = _heading(element)
        if heading is not None:
            if stream is not None:
                yield stream, " ".join(texts)
            stream, texts = _stream(heading), [heading]
            continue
        if stream is not None:
            texts.append(element.get_text(" ", strip=True))
    if stream is not None:
        yield stream, " ".join(texts)


def _exceptions(text: str) -> list[datetime.date]:
    """Dates a section says the round does not run ("sauf le 1er mai")."""
    today = datetime.date.today()
    dates: list[datetime.date] = []
    for day, month_name in _EXCEPT_RE.findall(text):
        month = recurrence.month(month_name)
        if month is None:
            continue
        for year in (today.year, today.year + 1):
            try:
                dates.append(datetime.date(year, month, int(day)))
            except ValueError:
                continue
    return dates


def _describe(content: Tag, source) -> Iterator[Schedule]:
    """One weekly Schedule per weekday named under each stream's heading."""
    seen: set[tuple[str, int]] = set()
    for stream, text in _sections(content):
        exclude = _exceptions(text)
        for word in _WORD_RE.findall(text):
            weekday = recurrence.weekday(word)
            if weekday is None or (stream, weekday) in seen:
                continue
            seen.add((stream, weekday))
            yield Schedule(
                stream,
                recurrence.next_weekday(weekday),
                recurrence.WEEKLY,
                _WEEKS_AHEAD,
                exclude=exclude,
            )


@final
class Source(BaseSource):
    TITLE = "Métropole Nice Côte d'Azur"
    DESCRIPTION = (
        "Source for Métropole Nice Côte d'Azur household waste and packaging "
        "collection days (communes with a fixed weekly schedule only; bulky waste "
        "and glass are not included)."
    )
    URL = "https://www.nicecotedazur.org"
    COUNTRY = "fr"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Krohler06"]

    # An unknown or unsupported commune raises from ArgumentLookup with the
    # supported communes as suggestions; an empty schedule still fails loudly.
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Aspremont": {"municipality": "Aspremont"},
        "Beaulieu-sur-Mer": {"municipality": "Beaulieu-sur-Mer"},
        "Cap d'Ail": {"municipality": "Cap d'Ail"},
        "Castagniers": {"municipality": "Castagniers"},
        "Colomars": {"municipality": "Colomars"},
        "Eze": {"municipality": "Èze"},
        "Falicon": {"municipality": "Falicon"},
        "La Trinite": {"municipality": "La Trinité"},
        "Le Broc": {"municipality": "Le Broc"},
        "Nice": {"municipality": "Nice"},
        "Saint-Blaise": {"municipality": "Saint-Blaise"},
        "Saint-Jean-Cap-Ferrat": {"municipality": "Saint-Jean-Cap-Ferrat"},
        "Saint-Laurent-du-Var": {"municipality": "Saint-Laurent-du-Var"},
        "Saint-Martin-du-Var": {"municipality": "Saint-Martin-du-Var"},
        "Villefranche-sur-Mer": {"municipality": "Villefranche-sur-Mer"},
    }

    PARAMS = (dropdown("municipality", SUPPORTED_COMMUNES, label="Municipality"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your commune. Only communes of the Métropole with one fixed "
            "set of collection weekdays are supported; communes with alternating "
            "weeks, seasonal periods or per-district rounds are not. Household "
            "waste and packaging (yellow bin) are included; bulky waste and glass "
            "are not."
        ),
        "fr": (
            "Sélectionnez votre commune. Seules les communes de la Métropole dont "
            "les jours de collecte sont fixes sont prises en charge ; les communes "
            "avec collecte une semaine sur deux, périodes saisonnières ou tournées "
            "par quartier ne le sont pas. Les ordures ménagères et les emballages "
            "(bac jaune) sont inclus ; les encombrants et le verre ne le sont pas."
        ),
    }

    retrieve = HttpGetRetriever(url=COLLECTION_URL)
    parse = parsers.HtmlParser(
        "div.collecte--block.commune", require=["div.collecte--block.commune"]
    )
    preprocess = Compose(
        ArgumentLookup(_communes, argument="municipality"),
        RecurrenceExpander(_describe),
    )
    transform = ICSTransformer(
        type_value_map={
            GENERAL_WASTE: wt.GENERAL_WASTE,
            RECYCLING: wt.RECYCLABLES,
        }
    )
