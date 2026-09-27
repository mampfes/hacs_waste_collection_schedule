import unicodedata
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer

_MUNICIPALITIES = (
    "candiac",
    "saint-constant",
    "chateauguay",
    "saint-isidore",
    "delson",
    "saint-mathieu",
    "la-prairie",
    "saint-philippe",
    "lery",
    "sainte-catherine",
    "mercier",
)
_SECTORS = ("nord-ouest", "est")


def _slug(name: str) -> str:
    """A municipality name as the site's region slug: "La Prairie" -> "la-prairie"."""
    decomposed = unicodedata.normalize("NFKD", name)
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return plain.replace(" ", "-").lower()


def _region(municipality: str, sector: str | None = None, **_) -> dict:
    """The calendar request; Châteauguay is split into two sectors."""
    region = _slug(municipality)
    if region not in _MUNICIPALITIES:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", municipality, _MUNICIPALITIES
        )
    if sector:
        sector = sector.lower()
        if region != "chateauguay":
            raise SourceArgumentException(
                "sector", f"Invalid sector for {region.capitalize()}"
            )
        if sector not in _SECTORS:
            raise SourceArgumentNotFoundWithSuggestions("sector", sector, _SECTORS)
        region = f"{region}-secteur-{sector}"
    return {"action": "ajaxJsYearCalendar", "region": region}


@final
class Source(BaseSource):
    TITLE = "MRC de Roussillon (QC)"
    DESCRIPTION = "Source script for info-collectes.ca/"
    URL = "https://info-collectes.ca/"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestName1": {"municipality": "La Prairie"},
        "TestName2": {"municipality": "candiac"},
        "TestName3": {"municipality": "chateauguay", "sector": "est"},
        "TestName4": {"municipality": "Delson"},
        "TestName5": {"municipality": "lery"},
    }

    PARAMS = (
        municipality(),
        text_field("sector", "Sector", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Your municipality in the MRC de Roussillon. Châteauguay also takes a sector: nord-ouest or est.",
        "fr": "Votre municipalité dans la MRC de Roussillon. Châteauguay prend aussi un secteur : nord-ouest ou est.",
    }

    retrieve = HttpPostRetriever(
        url="https://info-collectes.ca/wp/wp-admin/admin-ajax.php",
        data=_region,
    )
    # The year's collection days, each with the pictograms of that day's
    # rounds.
    parse = parsers.JsonParser("data")
    preprocess = ExplodeList("icone", into="round")
    transform = JsonTransformer(
        date_key="date",
        type_key="round",
        parse_date=date_parsers.for_format("%Y%m%d"),
        type_value_map={
            "garbage": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "organic": wt.ORGANIC,
            "greenWaste": wt.GARDEN_WASTE,
            "cardboard": wt.PAPER,
            "bulky": wt.BULKY_WASTE,
        },
    )
