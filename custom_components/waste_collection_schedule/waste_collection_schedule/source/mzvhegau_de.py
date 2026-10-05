from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city
from waste_collection_schedule.preprocessors import TextDatedBlocks
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer


def _strip_emoji(label: str) -> str:
    """A round without its pictogram prefix: "🗞️ Papier" -> "Papier"."""
    while label and not label[0].isalpha():
        label = label[1:].strip()
    return label


@final
class Source(BaseSource):
    TITLE = "MZV Hegau"
    DESCRIPTION = "Source for mzvhegau.de services for MZV Hegau, Germany."
    URL = "https://www.mzvhegau.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Engen": {"city": "Engen"},
        "Gai (Gailingen)": {"city": "Gai"},
        "GM (Gottmadingen)": {"city": "GM"},
    }

    PARAMS = (city(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your city/municipality shorthand in the MZV Hegau service area, e.g. Engen, Gai, GM.",
        "de": "Stadt/Gemeinde-Kürzel im MZV Hegau Verbandsgebiet eingeben, z.B. Engen, Gai, GM.",
    }

    retrieve = HttpGetRetriever(
        url="https://www.mzvhegau.de/wp-admin/admin-post.php",
        params=lambda city, **_: {
            "action": "mzv_ics_download",
            "slug": city.strip(),
            "whole_year": "1",
            "format": "text",
        },
    )
    # An unknown shorthand answers "Ungültiger Ort (Slug)." with HTTP 200.
    parse = parsers.ArgumentGuard(
        parsers.TextParser(),
        argument="city",
        contains="Abholtermine",
        suggestions=retrievers.Suggestions(
            "https://www.mzvhegau.de/wp-json/flexia/v2/pickups",
            pick=lambda response, **_: [
                entry["shorthand"] for entry in response.json() if "shorthand" in entry
            ],
        ),
    )
    # "29.09.2026: 🌱 Biomüll, 🗞️ Papier", one line per collection day.
    preprocess = TextDatedBlocks(
        block_pattern=(
            r"(?m)^(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4}):"
            r"[ \t]*(?P<labels>.+)$"
        ),
        label_separator=r",",
        normalise=_strip_emoji,
    )
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Biomüll": wt.ORGANIC,
            "Gelber Sack": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Grünschnitt": wt.GARDEN_WASTE,
            "Christbaum": wt.GARDEN_WASTE,
        }
    )
