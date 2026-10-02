from typing import ClassVar, final

from waste_collection_schedule import field_terms, parsers, regions, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

API_BASE = "https://heimatinfo-api-platform.azurewebsites.net"


def _area_id(response, *, commune, area=None):
    if response.status_code == 404:
        raise SourceArgumentNotFound("commune", commune)
    response.raise_for_status()
    areas = response.json()
    if not areas:
        raise SourceArgumentNotFound("commune", commune)
    if area is None and len(areas) == 1:
        return areas[0]["id"]
    if area is not None:
        match = next(
            (item for item in areas if item["name"].lower() == area.lower()), None
        )
        if match is not None:
            return match["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "area", area or "", [item["name"] for item in areas]
    )


@final
class Source(BaseSource):
    TITLE = "Heimat-Info"
    DESCRIPTION = "Source for Heimat-Info (heimat-info.de) waste collection schedules."
    URL = "https://www.heimat-info.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Gründau – Breitenborn": {"commune": "gruendau", "area": "Breitenborn"},
        "Gründau – Gettenbach": {"commune": "gruendau", "area": "Gettenbach"},
        "Salgen": {"commune": "salgen", "area": "Salgen"},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Open https://www.heimat-info.de, search for your commune, and navigate to "
        "Abfallkalender. The commune slug is the part of the URL after '/gemeinden/'. "
        "If the calendar shows multiple collection areas, pick yours from the list.",
        "de": "Öffnen Sie https://www.heimat-info.de, suchen Sie Ihre Gemeinde und navigieren "
        "Sie zum Abfallkalender. Der Gemeinde-Slug ist der Teil der URL nach "
        "'/gemeinden/'. Falls der Kalender mehrere Abholbereiche zeigt, wählen Sie "
        "Ihren aus der Liste.",
    }
    RAISE_ON_EMPTY = True

    PARAMS = (
        text_field(
            "commune",
            term=field_terms.MUNICIPALITY,
            coerce=lambda value: str(value).strip().lower(),
        ),
        text_field(
            "area",
            term=field_terms.DISTRICT,
            optional=True,
            coerce=lambda value: str(value).strip() or None,
        ),
    )
    REGIONS = regions.from_yaml("heimat_info_de", country="country", commune="commune")
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown area": {"commune": "gruendau", "area": "__unknown_area__"},
        "Area required": {"commune": "gruendau"},
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
    ]
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda commune, **_: (
                    f"{API_BASE}/communes/{commune}/garbagepickupareas"
                ),
                pick=_area_id,
                raise_for_status=False,
            ),
        ),
        url=lambda area_id, *, commune, **_: (
            f"{API_BASE}/communes/{commune}/garbagepickupareas/{area_id}/garbagepickupdates"
        ),
        raise_for_status=True,
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Residual": wt.GENERAL_WASTE,
            "Organic": wt.ORGANIC,
            "Paper": wt.PAPER,
            "Recyclable": wt.RECYCLABLES,
            "BulkyWaste": wt.BULKY_WASTE,
            "HazardousWaste": wt.HAZARDOUS,
        },
        carry_raw_label=True,
    )
