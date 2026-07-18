from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, PAPER, RECYCLABLES

# Lisboa's Amb_Reciclagem FeatureServer keys each collection area by name
# (NOME) and carries three fields of Portuguese weekday abbreviations, one
# per waste stream: DIAS_IND (general waste), DIAS_PAPEL (paper/cardboard),
# DIAS_EMBAL (packaging/recycling). Each field is a comma-separated list of
# one or more weekdays, all recurring weekly. The where clause is a
# source-specific attribute query; the PT abbreviation table is the API's own
# vocabulary (not a recurrence.weekday()-covered language form), and _describe()
# fans each field's weekdays out. ``parse`` is overridden as a method (rather
# than the plain ArcGisFeatureParser instance) only to reproduce the legacy
# "suggest known area names" behaviour on a no-match, a genuinely irregular
# extra lookup that no declarative parser expresses.

FEATURE_URL = "https://services.arcgis.com/1dSrzEWVQn5kHHyK/ArcGIS/rest/services/Amb_Reciclagem/FeatureServer/7"

# Portuguese weekday abbreviations, as returned by this API, to Python
# weekday() (0=Monday .. 6=Sunday).
_PT_WEEKDAYS = {
    "2ª": 0,  # Segunda-feira (Monday)
    "3ª": 1,  # Terça-feira (Tuesday)
    "4ª": 2,  # Quarta-feira (Wednesday)
    "5ª": 3,  # Quinta-feira (Thursday)
    "6ª": 4,  # Sexta-feira (Friday)
    "sáb": 5,  # Sábado (Saturday)
    "dom": 6,  # Domingo (Sunday)
}

# ArcGIS field -> waste-type key emitted for that field's weekdays.
_FIELDS = {
    "DIAS_IND": "Indiferenciado",
    "DIAS_PAPEL": "Papel e Cartão",
    "DIAS_EMBAL": "Embalagens",
}

_TYPE_MAP = {
    "Indiferenciado": GENERAL_WASTE,
    "Papel e Cartão": PAPER,
    "Embalagens": RECYCLABLES,
}

# Number of weekly collections to project (matches the legacy default).
WEEKS_AHEAD = 26


def _where(**params: Any) -> str:
    safe_name = params["area_name"].strip().replace("'", "''")
    return f"NOME = '{safe_name}'"


def _parse_days(days_str: str) -> list[int]:
    """Parse a Portuguese weekday-abbreviation string into weekday() ints."""
    if not days_str or not days_str.strip():
        return []
    weekdays = []
    for part in days_str.replace("feira", "").split(","):
        key = part.strip().lower()
        if key in _PT_WEEKDAYS:
            weekdays.append(_PT_WEEKDAYS[key])
    return weekdays


def _describe(attrs, source):
    for field, key in _FIELDS.items():
        for weekday in _parse_days(attrs.get(field, "")):
            yield Schedule(
                key, recurrence.next_weekday(weekday), recurrence.WEEKLY, WEEKS_AHEAD
            )


@final
class Source(BaseSource):
    TITLE = "Câmara Municipal de Lisboa"
    DESCRIPTION = "Source for waste collection schedules in Lisboa, Portugal."
    URL = "https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo"
    COUNTRY = "pt"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Restelo": {"area_name": "Restelo"},
        "Madredeus": {"area_name": "Madredeus"},
        "Alvito": {"area_name": "Alvito"},
        "Campo Ourique": {"area_name": "Campo Ourique"},
    }

    PARAMS = (text_field("area_name", "Collection Area"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo and "
            "search for your address on the map. The area name shown in the popup "
            "(e.g. 'Restelo', 'Madredeus') is the value to use."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL,
        where=_where,
        out_fields="NOME,DIAS_IND,DIAS_PAPEL,DIAS_EMBAL",
    )
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, area_name: str):
        super().__init__(area_name=area_name.strip())

    def parse(self, response, source: "Source | None" = None) -> list[dict]:
        features = ArcGisFeatureParser()(response, source)
        if not features:
            raise SourceArgumentNotFoundWithSuggestions(
                "area_name", self.params["area_name"], self._get_area_names()
            )
        return features

    def _get_area_names(self) -> list[str]:
        """Fetch all available area names for suggestions (best-effort)."""
        try:
            response = self.session.get(
                f"{FEATURE_URL}/query",
                params={
                    "where": "DIAS_IND <> ' '",
                    "outFields": "NOME",
                    "returnGeometry": "false",
                    "returnDistinctValues": "true",
                    "orderByFields": "NOME",
                    "f": "json",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return sorted(
                {
                    f["attributes"]["NOME"]
                    for f in data.get("features", [])
                    if f["attributes"].get("NOME")
                }
            )
        except Exception:
            return []
