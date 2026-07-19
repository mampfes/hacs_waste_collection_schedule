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
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.hartbeigraz.at"
_MENUONR = "225225009"

# Hart bei Graz suffixes the light-packaging round with the caller's
# address-specific collection zone (e.g. "Leichtverpackung LM1",
# "Leichtverpackung LM2"), which is not a fixed, enumerable set a
# type_value_map could exhaustively list. Stripping the zone code first lets
# the base label be mapped explicitly below.
_ZONE_SUFFIX_RE = re.compile(r"\s+LM\d+\s*$", re.IGNORECASE)


def _clean(label: str) -> str:
    return _ZONE_SUFFIX_RE.sub("", label.strip()).strip()


@final
class Source(BaseSource):
    TITLE = "Hart bei Graz"
    DESCRIPTION = "Source for Hart bei Graz, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        BULKY_WASTE,
        GARDEN_WASTE,
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Am Brühlwald 15": {"strasse": "Am Brühlwald", "hausnummer": "15"},
        "Alois Fleck-Gasse 1": {"strasse": "Alois Fleck-Gasse", "hausnummer": "1"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.hartbeigraz.at/Service/Muell, pick your street and "
            "house number from the dropdowns, and use the same values for "
            "'strasse' and 'hausnummer'."
        ),
        "de": (
            "Öffnen Sie https://www.hartbeigraz.at/Service/Muell, wählen Sie Ihre "
            "Straße und Hausnummer aus den Dropdown-Menüs, und verwenden Sie "
            "dieselben Werte für 'strasse' und 'hausnummer'."
        ),
    }

    # bdatum is a fixed "show everything" end date (not a rolling look-ahead
    # window), matching the legacy source. The list rendering paginates on
    # this install, so the parser must keep pulling pages instead of stopping
    # after the first one (see RiSKommunalParser(paginate_list=True) below);
    # the legacy fetch() override this replaces did the same by calling
    # _parse_list directly across every page.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": _MENUONR,
            "bdatum": "31.12.9999",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url="https://www.hartbeigraz.at/Service/Muell",
        max_pages=25,
    )
    parse = RiSKommunalParser(paginate_list=True)

    # Restmüll, Bioabfall, Altpapier and Sperrmüll all resolve via the shared
    # vocabulary. "Grün- und Strauchschnittsammlung" and "Strauchschnittabholung"
    # are garden-waste rounds with no matching alias. After the zone-code
    # suffix is stripped, "Leichtverpackung" (this install's Gelber Sack/LVP
    # equivalent) also needs an explicit entry.
    transform = ICSTransformer(
        clean=_clean,
        type_value_map={
            "Grün- und Strauchschnittsammlung": GARDEN_WASTE,
            "Strauchschnittabholung": GARDEN_WASTE,
            "Leichtverpackung": RECYCLABLES,
        },
    )
