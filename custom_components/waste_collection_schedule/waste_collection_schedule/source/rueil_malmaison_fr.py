import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import coords
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import FanOutRetriever, Request
from waste_collection_schedule.transformers import ICSTransformer

_API = "https://opendata.hauts-de-seine.fr/api/explore/v2.1/catalog/datasets"

# waste type label -> Opendatasoft dataset of the collection zones
_DATASETS = {
    "Ordures Ménagères": "fr-219200631-collecte-des-ordures-menageres",
    "Emballages": "fr-219200631-collecte-des-emballages",
    "Verre": "fr-219200631-collecte-du-verre",
    "Déchets Végétaux": "fr-219200631-collecte-des-dechets-vegetaux",
    "Encombrants": "fr-219200631-encombrant",
}


def _weekdays(jours: str) -> list[int]:
    """``"Mardi, Vendredi"`` -> ``[1, 4]``; ``"Pas de collecte"`` -> ``[]``."""
    days = (
        recurrence.weekday(name.strip()) for name in re.split(r"[,/&]|\bet\b", jours)
    )
    return [day for day in days if day is not None]


def _season(perioann: str, year: int) -> tuple[datetime.date, datetime.date] | None:
    """The collection window of one year: "De mi-mars à mi-décembre" is
    15 March to 15 December, "Toute l'année" the whole year."""
    text = perioann.lower()
    if "pas de collecte" in text:
        return None
    if "mars" in text and "d" in text.split("mars", 1)[1]:
        start = datetime.date(year, 3, 15 if "mi-mars" in text else 1)
        return start, datetime.date(year, 12, 15)
    return datetime.date(year, 1, 1), datetime.date(year, 12, 31)


def _describe(record, source):
    """One windowed weekly Schedule per weekday and year, ``frequenc`` fixing the
    ISO week parity ("semaine paire" / "semaine impaire")."""
    frequency = record["frequenc"].lower()
    if "pas de collecte" in frequency or "non concerné" in frequency:
        return
    if "impaire" in frequency:
        parity = "odd"
    elif "paire" in frequency:
        parity = "even"
    else:
        parity = None
    today = datetime.date.today()
    horizon = datetime.date(today.year + 1, today.month, today.day)
    for weekday in _weekdays(record["jours"]):
        for year in (today.year, today.year + 1):
            window = _season(record["perioann"], year)
            if window is None:
                continue
            first = max(window[0], today)
            last = min(window[1], horizon)
            if first > last:
                continue
            yield Schedule(
                record["kind"],
                recurrence.next_weekday(weekday, on_or_after=first),
                not_before=first,
                until=last,
                iso_week_parity=parity,
            )


@final
class Source(BaseSource):
    TITLE = "Rueil-Malmaison"
    DESCRIPTION = "Source for waste collection schedule in Rueil-Malmaison, France."
    URL = "https://www.rueil-malmaison.fr"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mairie de Rueil-Malmaison": {"lat": 48.8768, "lon": 2.1875},
        "Quartier Plaine-Gare": {"lat": 48.8860, "lon": 2.1730},
    }

    PARAMS = (coords(),)

    HOWTO: ClassVar[dict] = {
        "fr": (
            "Choisissez votre adresse sur la carte. Les zones de collecte "
            "proviennent des données ouvertes des Hauts-de-Seine "
            "(opendata.hauts-de-seine.fr)."
        ),
        "en": (
            "Pick your address on the map. The collection zones come from the "
            "Hauts-de-Seine open data portal (opendata.hauts-de-seine.fr)."
        ),
    }

    retrieve = FanOutRetriever(
        targets=lambda source, _context: list(_DATASETS),
        fetch=Request(
            lambda kind, _context, **_: f"{_API}/{_DATASETS[kind]}/records",
            params=lambda kind, _context, lat, lon, **_: {
                "select": f'frequenc,jours,perioann,"{kind}" as kind',
                "where": f"intersects(geo_shape, geom'POINT({float(lon)} {float(lat)})')",
                "limit": 20,
            },
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser("results"))
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "Ordures Ménagères": wt.GENERAL_WASTE,
            "Emballages": wt.RECYCLABLES,
            "Verre": wt.GLASS,
            "Déchets Végétaux": wt.GARDEN_WASTE,
            "Encombrants": wt.BULKY_WASTE,
        }
    )
