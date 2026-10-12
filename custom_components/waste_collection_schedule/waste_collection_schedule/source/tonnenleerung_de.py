from typing import Any, ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.date_parsers import for_format
from waste_collection_schedule.transformers import RowTransformer

# The page lists every bin's dates as JSON in an inline <script id="leerungsdaten">.
_TYPE_MAP = {
    "blau": wt.PAPER,
    "gelb": wt.RECYCLABLES,
    "braun": wt.ORGANIC,
    "grau": wt.GENERAL_WASTE,
    "grau4": wt.GENERAL_WASTE,
}


def _path(value: Any) -> str:
    """Reduce a full URL or a leading-slash path to the bare page path."""
    path = str(value).strip()
    if "tonnenleerung.de" in path:
        path = path.split("tonnenleerung.de", 1)[1]
    return path.lstrip("/")


@final
class Source(BaseSource):
    TITLE = "tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen"
    DESCRIPTION = (
        "Source for tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen."
    )
    URL = "https://tonnenleerung.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "nd-sob/neuburg-donau/adalbert-stifter-strasse/": {
            "url": "nd-sob/neuburg-donau/adalbert-stifter-strasse/"
        },
        "aic-fdb/affing/": {"url": "https://tonnenleerung.de/aic-fdb/affing"},
        "nd-sob/schrobenhausen/albertus-magnus-weg/": {
            "url": "/nd-sob/schrobenhausen/albertus-magnus-weg/"
        },
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Open your street (or village) on https://tonnenleerung.de and copy the address of the page, e.g. `https://tonnenleerung.de/aic-fdb/affing`. The part after the domain (`aic-fdb/affing`) also works.",
        "de": "Öffne deine Straße (oder deinen Ort) auf https://tonnenleerung.de und kopiere die Adresse der Seite, z. B. `https://tonnenleerung.de/aic-fdb/affing`. Der Teil nach der Domain (`aic-fdb/affing`) funktioniert ebenfalls.",
    }

    PARAMS = (text_field("url", "URL", coerce=_path),)

    retrieve = retrievers.Request(lambda url, **_: f"https://tonnenleerung.de/{url}")
    parse = parsers.KeyedDateListsParser(
        fields=_TYPE_MAP, from_element='script[type="application/json"]#leerungsdaten'
    )
    preprocess = preprocessors.Deduplicate()
    transform = RowTransformer(
        parse_date=for_format("%Y-%m-%d"),
        type_value_map=_TYPE_MAP,
    )
