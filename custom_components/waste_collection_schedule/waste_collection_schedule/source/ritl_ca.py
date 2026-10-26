import re
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import field_terms as ft
from waste_collection_schedule import (
    lookups,
    parsers,
    preprocessors,
    regions,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.MarkedPdfCalendar import MarkedPdfCalendarParser
from waste_collection_schedule.transformers import JsonTransformer

# Stable municipal landing pages. PDF filenames/years are discovered at runtime.
_PAGES = {
    "Ivry-sur-le-Lac": {"all": "ivry-sur-le-lac"},
    "Lac-Supérieur": {
        "Secteur 1": "lac-superieur-secteur-a",
        "Secteur 2": "lac-superieur-secteur-b",
    },
    "Lantier": {"all": "lantier"},
    "Mont-Blanc": {
        "Secteur Est": "saint-faustin-lac-carre-secteur-est",
        "Secteur Ouest": "saint-faustin-lac-carre-secteur-ouest",
    },
    "Sainte-Agathe-des-Monts": {
        "Secteur Centre-ville": "ville-de-sainte-agathe-des-monts",
        "Secteur Nord": "ville-de-sainte-agathe-des-monts-secteur-nord",
        "Secteur Sud / Fatima": "ville-de-sainte-agathe-des-monts-secteur-sud-fatima",
    },
    "Sainte-Lucie-des-Laurentides": {"all": "sainte-lucie-des-laurentides"},
    "Val-des-Lacs": {"all": "val-des-lacs"},
}


def _sector(value):
    normal = lookups.normalize_loose(str(value or ""))
    if normal.startswith("secteur "):
        normal = normal[len("secteur ") :]
    return {"a": "1", "b": "2", "sud": "sud fatima", "fatima": "sud fatima"}.get(
        normal, normal
    )


def _page_url(municipality, sector=None, **_):
    town = next(
        (
            name
            for name in _PAGES
            if lookups.normalize_loose(name) == lookups.normalize_loose(municipality)
        ),
        None,
    )
    if town is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", municipality, list(_PAGES)
        )
    choices = _PAGES[town]
    if "all" in choices:
        selected = "all"
    else:
        selected = next(
            (name for name in choices if _sector(name) == _sector(sector)), None
        )
        if selected is None:
            raise SourceArgumentNotFoundWithSuggestions("sector", sector, list(choices))
    return "https://ritl.ca/calendrier-" + choices[selected] + "/"


_WEEKDAYS = {"lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4}
_MONTHS = {
    "janv": 1,
    "fevr": 2,
    "mars": 3,
    "avr": 4,
    "mai": 5,
    "juin": 6,
    "juil": 7,
    "aout": 8,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _keep_sector(record, source):
    if not date.today() <= record["date"] <= date.today() + timedelta(days=365):
        return False
    if source is None:
        raise ValueError("RITL sector filtering requires source parameters")
    text = lookups.normalize_loose(record["calendar_text"])
    routes = {
        _sector(area): _WEEKDAYS[weekday]
        for weekday, area in re.findall(
            r"\b(lundi|mardi|mercredi|jeudi|vendredi) (?:secteur )?(sud fatima|centre ville|nord|est|ouest)\b",
            text,
        )
    }
    if not routes:
        return True  # A calendar dedicated to one municipality/sector.
    sector = _sector(source.params.get("sector"))
    if sector not in routes:
        raise ValueError("The PDF has no published weekday for this sector")
    if record["date"].weekday() == routes[sector]:
        return True
    # Explicit, sector-labelled exceptions printed next to the calendar.
    for day, month, year, area in re.findall(
        r"\b(\d{1,2}) (janv|fevr|mars|avr|mai|juin|juil|aout|sept|oct|nov|dec)\w* (20\d{2}) (?:secteur )?(sud fatima|centre ville|nord|est|ouest)\b",
        text,
    ):
        if _sector(area) == sector and record["date"] == date(
            int(year), _MONTHS[month], int(day)
        ):
            return True
    # A crossed-out collection moved to an otherwise unused weekday. The
    # replacement date is an actual printed marker, never a projected date.
    if record["date"].weekday() not in routes.values():
        for cancelled, replacement in record["next_marked_after_cancelled"].items():
            if (
                cancelled.weekday() == routes[sector]
                and replacement == record["date"]
                and (replacement - cancelled).days <= 7
            ):
                return True
    return False


@final
class Source(BaseSource):
    TITLE = "RITL"
    DESCRIPTION = (
        "Collection calendars published by Régie intermunicipale des Trois-Lacs."
    )
    URL = "https://ritl.ca/"
    COUNTRY = "ca"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Jean-PascalComeau"]
    TEST_CASES: ClassVar[dict] = {
        name + " " + sector: {
            "municipality": name,
            "sector": sector if sector != "all" else None,
        }
        for name, sectors in _PAGES.items()
        for sector in sectors
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Former Val-David calendar": {
            "municipality": "Val-David",
            "sector": "Secteur 2",
        },
        "Unknown Lac-Supérieur sector": {
            "municipality": "Lac-Supérieur",
            "sector": "unknown",
        },
    }
    PARAMS = (municipality(), text_field("sector", term=ft.WASTE_SECTOR, optional=True))
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Choose a municipality and sector listed under Calendriers de collecte at https://ritl.ca/. The former ICS export has been replaced by the published annual PDFs. Montcalm, Val-David and Val-Morin have no calendar in the current RITL listing. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    REGIONS = tuple(
        regions.region(
            name if sector == "all" else name + " " + sector,
            url="https://ritl.ca/calendrier-" + slug + "/",
            municipality=name,
            sector=sector if sector != "all" else None,
        )
        for name, sectors in _PAGES.items()
        for sector, slug in sectors.items()
    )
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _page_url, pick=retrievers.yearly_links(r"(20\d{2})[^/]*\.pdf")
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda target, urls, **_: target),
    )
    parse = parsers.EachResponse(
        MarkedPdfCalendarParser(
            pages=(0,),
            months=(
                "Janvier",
                "Février",
                "Mars",
                "Avril",
                "Mai",
                "Juin",
                "Juillet",
                "Août",
                "Septembre",
                "Octobre",
                "Novembre",
                "Décembre",
            ),
            weekdays=("L", "M", "M", "J", "V"),
            year_pattern=r"CALENDRIER DE COLLECTES (20\d{2})",
            allow_unmarked_missing_days=True,
            cancelled_colors=((0, 0.89, 0.51, 0),),
            colors={
                "general": ((0, 0, 0, 1),),
                "organic": ((0.4, 0.6, 0.88, 0.34),),
                "recycling": ((1, 0.85, 0, 0),),
            },
        )
    )
    preprocess = preprocessors.RowFilter(_keep_sector)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "general": wt.GENERAL_WASTE,
            "organic": wt.ORGANIC,
            "recycling": wt.RECYCLABLES,
        },
    )
