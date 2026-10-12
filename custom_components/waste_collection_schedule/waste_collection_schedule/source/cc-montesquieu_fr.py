"""Communauté de Communes de Montesquieu (Gironde), France.

The collection page lists, per commune, the weekday of the household-waste bin
and of the yellow (recycling) bin in an HTML table, and links one yearly PDF
poster with the dates of the green-waste and bulky-item rounds, where blocks of
communes share a date. The retriever fetches the page and every poster from the
current year on; the page's table is expanded into weekly collections and the
poster is read by ``PdfPlaceColumns``.
"""

from collections.abc import Iterable
from typing import Any, ClassVar, final

from bs4.element import Tag
from waste_collection_schedule import lookups, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.preprocessors import ArgumentLookup, Compose
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfPlaceColumns import (
    PlaceColumnsParser,
    PlaceDate,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets"
_PDF_PATTERN = r"PLANNING-DECHETS-VERTS-ENCOMBRANTS-(\d{4})\.pdf"

COMMUNES = (
    "Ayguemorte-les-Graves",
    "Beautiran",
    "Cabanac-et-Villagrains",
    "Cadaujac",
    "Castres-Gironde",
    "Isle Saint-Georges",
    "La Brède",
    "Léognan",
    "Martillac",
    "Saint-Médard-d'Eyrans",
    "Saint-Morillon",
    "Saint-Selve",
    "Saucats",
)

# The table's columns after the commune: the household-waste bin, the yellow bin.
_TABLE_KEYS = ("general", "recycling")
# The poster's columns, left to right: its heading and the key its rows carry.
_POSTER_COLUMNS = {"garden": "DÉCHETS VERTS", "bulky": "ENCOMBRANTS"}
# Weekly weekday collections are projected this many weeks ahead.
_WEEKS = 20


def _canonical(name: str) -> str:
    """The commune as ``COMMUNES`` spells it (the page varies case and hyphens)."""
    wanted = lookups.normalize_loose(name)
    return next(
        (c for c in COMMUNES if lookups.normalize_loose(c) == wanted), name.strip()
    )


def _weekly(weekday_name: str) -> list[Any]:
    weekday = recurrence.weekday(weekday_name)
    if weekday is None:
        raise ValueError(f"unknown collection weekday {weekday_name!r}")
    return recurrence.recurring(
        recurrence.next_weekday(weekday), recurrence.WEEKLY, _WEEKS
    )


def _table_rows(table: Tag) -> Iterable[tuple[str, list[tuple[Any, str]]]]:
    """``(commune, [(date, key)])`` for each row of the page's collection table.

    The page's HTML is malformed (the first row's ``<tr>`` is missing), so the
    cells are chunked by the header's column count rather than read by row.
    """
    width = len(table.select("thead th"))
    cells = [cell.get_text(strip=True) for cell in table.select("tbody td")]
    for start in range(0, len(cells) - width + 1, width):
        name, *days = cells[start : start + width]
        yield (
            _canonical(name),
            [
                (day, key)
                for text, key in zip(days, _TABLE_KEYS, strict=False)
                for day in _weekly(text)
            ],
        )


def _planning(records: Any, source: Any = None) -> dict[str, list[tuple[Any, str]]]:
    """Every commune's rows from the page's table and the posters' dated blocks."""
    planning: dict[str, list[tuple[Any, str]]] = {}
    for record in records:
        if isinstance(record, PlaceDate):
            planning.setdefault(record.place, []).append((record.date, record.label))
        elif isinstance(record, Tag) and "ordures ménagères" in str(record):
            for commune, rows in _table_rows(record):
                planning.setdefault(commune, []).extend(rows)
    return {
        commune: sorted(set(rows))
        for commune, rows in planning.items()
        if commune in COMMUNES and rows
    }


def _flatten(resolved: Iterable[Any], source: Any = None) -> Iterable[Any]:
    for rows in resolved:
        yield from rows


@final
class Source(BaseSource):
    TITLE = "Communauté de Communes de Montesquieu"
    DESCRIPTION = "Source for the waste collection of the Communauté de Communes de Montesquieu (Gironde)."
    URL = "https://www.cc-montesquieu.fr/"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {c: {"commune": c} for c in COMMUNES}

    PARAMS = (municipality("commune"),)

    REGIONS = tuple(region(c, commune=c) for c in COMMUNES)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your commune as it is listed on "
            "https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets "
            "(for example 'La Brède' or 'Saint-Médard-d'Eyrans')."
        ),
        "fr": (
            "Saisissez votre commune telle qu'elle figure sur "
            "https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets "
            "(par exemple « La Brède » ou « Saint-Médard-d'Eyrans »)."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL, pick=retrievers.yearly_links(_PDF_PATTERN)
        ),
        targets=lambda source, urls: [_INDEX_URL, *urls],
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.ByBodyPrefix(
            {
                "%PDF": PlaceColumnsParser(
                    places=COMMUNES,
                    columns=_POSTER_COLUMNS,
                    year_pattern=r"PLANNING\s+(\d{4})",
                )
            },
            default=parsers.HtmlParser("table"),
        )
    )
    preprocess = Compose(ArgumentLookup(_planning, argument="commune"), _flatten)
    transform = ICSTransformer(
        type_value_map={
            "general": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
            "bulky": wt.BULKY_WASTE,
        }
    )
