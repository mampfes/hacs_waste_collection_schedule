import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

_BASE_URL = "https://www.imst.gv.at"
_MENUONR = "222722602"

# Imst suffixes some labels with the caller's address-specific collection zone
# (e.g. "Restmüllzone 6", "Biomüll Zone 2"), which is not a fixed, enumerable
# set of strings a type_value_map could exhaustively list. Stripping the
# variable "zone N" / "Abholung" suffix first lets the base label resolve
# against the shared vocabulary (Restmüll, Biomüll) instead.
_ZONE_SUFFIX_RE = re.compile(r"\s*zone\s*\d+\s*$", re.IGNORECASE)


def _clean(label: str) -> str:
    text = _ZONE_SUFFIX_RE.sub("", label.strip()).strip()
    if text.lower().endswith(" abholung"):
        text = text[: -len(" abholung")].strip()
    return text


@final
class Source(BaseSource):
    TITLE = "Imst"
    DESCRIPTION = "Waste collection schedule for Stadtgemeinde Imst, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Auf Arzill 154": {
            "strasse": "Auf Arzill",
            "hausnummer": "154",
        },
        "Adlerweg 2": {
            "strasse": "Adlerweg",
            "hausnummer": "2",
        },
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.imst.gv.at/Muellabfuhrplaene_1, pick your street and "
            "house number from the dropdowns, and use the same values for "
            "'strasse' and 'hausnummer'."
        ),
        "de": (
            "Öffnen Sie https://www.imst.gv.at/Muellabfuhrplaene_1, wählen Sie Ihre "
            "Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
            "dieselben Werte für 'strasse' und 'hausnummer'."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": _MENUONR,
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url="https://www.imst.gv.at/Muellabfuhrplaene_1",
    )
    parse = RiSKommunalParser()

    # After the zone/Abholung suffix is stripped, only the plural "Gelbe
    # Säcke" needs an explicit entry; every other cleaned label (Restmüll,
    # Biomüll, Altpapier, Sperrmüll, Problemstoff, Altglas, Grünschnitt) is
    # classified by the shared vocabulary.
    transform = ICSTransformer(
        clean=_clean,
        type_value_map={
            "Gelbe Säcke": RECYCLABLES,
        },
    )
