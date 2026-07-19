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
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.buermoos.at"
_SELECTION_URL = "https://www.buermoos.at/Service/Aktuelles/Muellkalender"

# Bürmoos suffixes several labels with a collection-frequency phrase whose
# number varies by street/zone (e.g. "GELB - 1-wöchentliche Entleerung",
# "Altpapier 6 - wöchentlich"), so it is not a fixed, enumerable set a
# type_value_map could exhaustively list. Stripping the variable suffix first
# lets the remaining label resolve via the shared vocabulary or an explicit
# zone-colour entry below.
_FREQUENCY_SUFFIX_RE = re.compile(
    r"\s*-?\s*\d+[\s-]*w[oö]chentliche?(?:\s+entleerung)?\s*$", re.IGNORECASE
)


def _clean(label: str) -> str:
    return _FREQUENCY_SUFFIX_RE.sub("", label.strip()).strip()


@final
class Source(BaseSource):
    TITLE = "Gemeinde Bürmoos"
    DESCRIPTION = "Source for Gemeinde Bürmoos, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Birkenstraße 76a": {"strasse": "Birkenstraße", "hausnummer": "76a"},
        "Almweg 2": {"strasse": "Almweg", "hausnummer": "2"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.buermoos.at/Service/Aktuelles/Muellkalender, pick your "
            "street and house number from the dropdowns, and use the same values for "
            "'strasse' and 'hausnummer'."
        ),
        "de": (
            "Öffnen Sie https://www.buermoos.at/Service/Aktuelles/Muellkalender, wählen "
            "Sie Ihre Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
            "dieselben Werte für 'strasse' und 'hausnummer'."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "219233420",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=_SELECTION_URL,
        lookahead_days=365,
        max_pages=30,
    )
    parse = RiSKommunalParser(lookahead_days=365)

    # After the frequency suffix is stripped, "Altpapier" and "Gelber Sack"
    # resolve via the shared vocabulary; the zone-colour codes (GELB/ROT/WEIß)
    # and the LVP-Behälter labels have no equivalent alias and are mapped
    # explicitly, as is "Biomüllabfuhr" (a compound the "Biomüll" alias does
    # not cover).
    transform = ICSTransformer(
        clean=_clean,
        type_value_map={
            "GELB": RECYCLABLES,
            "ROT": GENERAL_WASTE,
            "WEIß": GENERAL_WASTE,
            "LVP-Behälter Wohnanlagen und Betriebe": RECYCLABLES,
            "LVP-Behälter Betriebe - Wohnanlagen & Betriebe": RECYCLABLES,
            "Biomüllabfuhr": ORGANIC,
        },
    )
