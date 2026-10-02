from typing import Any, ClassVar, TypedDict, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.transformers import JsonTransformer

# secteur_nom values of the open data dataset.
SECTORS = [
    "Angoulins-sur-Mer",
    "Aytré",
    "Bourgneuf",
    "Châtelaillon Zone verte (Secteur Est)",
    "Châtelaillon Zone violette (Secteur littoral)",
    "Châtelaillon-Plage",
    "Clavette",
    "Croix-Chapeau",
    "Dompierre-sur-Mer",
    "Esnandes",
    "L'Houmeau",
    "La Jarne",
    "La Jarrie",
    "La Rochelle Secteur A",
    "La Rochelle Secteur B",
    "La Rochelle Secteur C",
    "La Rochelle Secteur D",
    "La Rochelle Secteur E",
    "La Rochelle Secteur F",
    "La Rochelle Secteur G",
    "La Rochelle Secteur H",
    "La Rochelle Secteur I",
    "La Rochelle Secteur J",
    "La Rochelle Secteur K",
    "Lagord",
    "Marsilly",
    "Montroy",
    "Nieul-sur-Mer",
    "Périgny",
    "Puilboreau",
    "Saint-Christophe",
    "Saint-Médard d'Aunis",
    "Saint-Rogatien",
    "Saint-Vivien",
    "Saint-Xandre",
    "Sainte-Soulle",
    "Salles-sur-Mer",
    "Secteur L",
    "Secteur M",
    "Secteur N",
    "Secteur O",
    "Thairé",
    "Vérines",
    "Yves",
]


class _Fields(TypedDict):
    jour: str
    collecte_type: str
    secteur_nom: str


class _Record(TypedDict):
    fields: _Fields


def _keep_sector(record: _Record, source: Any) -> bool:
    return record["fields"]["secteur_nom"] == source.params["sector"]


@final
class Source(BaseSource):
    TITLE = "Agglomération de La Rochelle"
    DESCRIPTION = "Source for waste collection in La Rochelle agglomeration."
    URL = "https://www.agglo-larochelle.fr"
    COUNTRY = "fr"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@fanfounet"]

    # The API mishandles non-ASCII refine filters and an encoded comma in
    # "fields", so the whole dataset is fetched and filtered on the sector.
    API_URL = (
        "https://opendata.agglo-larochelle.fr/d4c/api/records/1.0/search/"
        "?dataset=dechet_-_prochaines_dates_de_collecte"
        "&rows=1000&fields=jour,collecte_type,secteur_nom"
    )

    TEST_CASES: ClassVar[dict] = {
        "La Rochelle Secteur A": {"sector": "La Rochelle Secteur A"},
        "Aytré": {"sector": "Aytré"},
        "Châtelaillon Zone verte": {
            "sector": "Châtelaillon Zone verte (Secteur Est)",
        },
    }

    PARAMS = (dropdown("sector", SECTORS, label="Sector"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your municipality, or for La Rochelle, Châtelaillon-Plage "
            "and the sectors L to O, your collection sector. Find it on the "
            "map: https://opendata.agglo-larochelle.fr/visualisation/map/"
            "?id=dechet_-_prochaines_dates_de_collecte"
        ),
        "fr": (
            "Sélectionnez votre commune ou, pour La Rochelle, "
            "Châtelaillon-Plage et les secteurs L à O, votre secteur de "
            "collecte. Retrouvez-le sur la carte : "
            "https://opendata.agglo-larochelle.fr/visualisation/map/"
            "?id=dechet_-_prochaines_dates_de_collecte"
        ),
    }

    RAISE_ON_EMPTY = True

    parse = parsers.JsonParser("records", shape=list[_Record])

    preprocess = RowFilter(_keep_sector)

    transform = JsonTransformer(
        date_key=lambda record: record["fields"]["jour"],
        type_key=lambda record: record["fields"]["collecte_type"],
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Ordures ménagères": wt.GENERAL_WASTE,
            "Emballages recyclables": wt.RECYCLABLES,
        },
    )
