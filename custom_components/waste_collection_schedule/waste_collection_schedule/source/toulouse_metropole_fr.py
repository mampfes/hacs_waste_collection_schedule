import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

# Opendatasoft API v2.1: one dataset per flux (household waste, selective collection).
_BASE = "https://data.toulouse-metropole.fr/api/explore/v2.1/catalog/datasets"
_DATASETS = (
    f"{_BASE}/dechets-collecte-des-ordures-menageres/records",
    f"{_BASE}/dechets-collecte-selective/records",
)

# How many weeks ahead to generate dates
_WEEKS_AHEAD = 8

_WORD = re.compile(r"[^\W\d_]+")


def _describe(record: dict, source=None):
    """One Schedule per weekday named in the 'infobulle_pdi' field.

    Examples: "Vendredi", "Mercredi semaine paire", "Le lundi, mercredi et
    vendredi", "7 jours / 7".
    """
    infobulle = (record.get("infobulle_pdi") or "").strip().lower()
    flux = (record.get("flux") or "").strip()
    if not infobulle or not flux:
        return

    if "7 jours / 7" in infobulle:
        weekdays = list(range(7))
    else:
        weekdays = [
            wd
            for word in _WORD.findall(infobulle)
            if (wd := recurrence.weekday(word)) is not None
        ]

    parity = None
    if "semaine impaire" in infobulle:
        parity = "odd"
    elif "semaine paire" in infobulle:
        parity = "even"

    for weekday in weekdays:
        # Legacy behaviour: the first date is strictly after today.
        start = recurrence.next_weekday(
            weekday, on_or_after=datetime.date.today() + datetime.timedelta(days=1)
        )
        yield Schedule(
            flux,
            start,
            recurrence.WEEKLY,
            _WEEKS_AHEAD,
            iso_week_parity=parity,
        )


@final
class Source(BaseSource):
    TITLE = "Toulouse Métropole"
    DESCRIPTION = (
        "Source pour la collecte des déchets de Toulouse Métropole (37 communes)."
    )
    URL = "https://data.toulouse-metropole.fr"
    COUNTRY = "fr"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@fangedhex"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        # Single-day OM (Lundi + Mardi) + bi-weekly CS (Mercredi semaine paire)
        "Colomiers - Avenue Henri Guillaumet": {
            "street_name": "Avenue Henri Guillaumet",
        },
        # Multi-day OM "Le lundi, mercredi et vendredi" + single-day OM "Jeudi" + CS "Jeudi"
        "Toulouse - Rue de la Paix": {
            "street_name": "Rue de la Paix",
        },
        # Bi-weekly CS "Mercredi semaine paire" (even ISO weeks)
        "Chemin Vié (bi-weekly CS)": {
            "street_name": "Chemin Vié",
        },
        # Single-day OM "Vendredi" + single-day OM "Lundi" + bi-weekly CS "Jeudi semaine impaire"
        "Route de Fonbeauzard": {
            "street_name": "Route de Fonbeauzard",
        },
        # 3-day multi-day OM "Le lundi, mercredi et vendredi" + CS "Jeudi"
        "Toulouse - Rue Sainte-Thérèse": {
            "street_name": "Rue Sainte-Thérèse",
        },
        # Daily OM "7 jours / 7" (every day of the week)
        "Toulouse - Rue des Lois": {
            "street_name": "Rue des Lois",
        },
    }

    PARAMS = (street(field="street_name"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name exactly as it appears on the Toulouse Métropole open data portal. "
            "You can look it up at: "
            "https://data.toulouse-metropole.fr/explore/dataset/dechets-collecte-des-ordures-menageres/table/"
        ),
        "fr": (
            "Saisissez le nom de votre voie tel qu'il apparaît sur le portail open data de Toulouse Métropole. "
            "Vous pouvez le retrouver ici : "
            "https://data.toulouse-metropole.fr/explore/dataset/dechets-collecte-des-ordures-menageres/table/"
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        targets=lambda source, context: _DATASETS,
        fetch=retrievers.Request(
            lambda url, context, **_: url,
            params=lambda url, context, street_name, **_: {
                "limit": 20,
                "refine": f'libelle_voie:"{street_name.strip()}"',
                "select": "libelle_voie,infobulle_pdi,flux",
            },
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser("results"))
    preprocess = Compose(RecurrenceExpander(_describe), Deduplicate())
    transform = ICSTransformer(
        type_value_map={
            "Ordure ménagère": wt.GENERAL_WASTE,
            "Collecte sélective": wt.RECYCLABLES,
        }
    )
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]
