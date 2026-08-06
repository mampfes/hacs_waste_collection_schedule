from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.berndorf.gv.at"
_SELECTION_URL = (
    "https://www.berndorf.gv.at/Buergerservice/Aktuelles/Muellabfuhrtermine"
)

# Berndorf's calendar labels every collection with an "Abfuhrtermine Berndorf "
# site-name prefix (e.g. "Abfuhrtermine Berndorf Restmüll"), which is not a
# fixed, enumerable set a type_value_map could exhaustively list. Stripping the
# constant prefix first lets the base label (Restmüll, Biotonne, Altpapier)
# resolve against the shared vocabulary.
_PREFIX = "abfuhrtermine berndorf "


def _clean(label: str) -> str:
    text = label.strip()
    if text.lower().startswith(_PREFIX):
        text = text[len(_PREFIX) :].strip()
    return text


@final
class Source(BaseSource):
    TITLE = "Stadtgemeinde Berndorf"
    DESCRIPTION = "Source for Stadtgemeinde Berndorf, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    # The vocabulary this feed actually produces, derived by replaying the
    # recorded cassette. Declared explicitly because most of these labels are
    # resolved by the shared vocabulary rather than listed in type_value_map,
    # so the auto-derived set would be incomplete.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Albertstraße 1": {"strasse": "Albertstraße", "hausnummer": "1"},
        "Alleegasse 2": {"strasse": "Alleegasse", "hausnummer": "2"},
        "Mühlgasse 1": {"strasse": "Mühlgasse", "hausnummer": "1"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.berndorf.gv.at/Buergerservice/Aktuelles/"
            "Muellabfuhrtermine, pick your street and house number from the "
            "dropdowns, and use the same values for 'strasse' and 'hausnummer'."
        ),
        "de": (
            "Öffnen Sie https://www.berndorf.gv.at/Buergerservice/Aktuelles/"
            "Muellabfuhrtermine, wählen Sie Ihre Straße und Hausnummer aus den "
            "Dropdown-Menüs, und verwenden Sie dieselben Werte für 'strasse' "
            "und 'hausnummer'."
        ),
    }

    # Berndorf has four collection zones and a wine-tavern calendar, and asking
    # for none of them returned all five merged: every user saw all four zones'
    # rounds plus fifteen Heurigen opening seasons. There is no query parameter
    # that filters the table rendering, because the town's waste calendar is
    # address-based: the street and house number resolve to the zone's
    # ``typids``, and asking for one switches the install to its JavaScript
    # month grid, which the shared parser now reads as a third rendering.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "226080602",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=_SELECTION_URL,
    )
    parse = RiSKommunalParser()

    # After the site-name prefix is stripped, only the plural "Gelbe Säcke"
    # and the ash bin (Aschetonne, no canonical equivalent; collected
    # alongside residual waste) need an explicit entry; every other cleaned
    # label (Restmüll, Biotonne, Bioabfall, Biomüll, Altpapier, Papier, Gelber
    # Sack, Gelbe Tonne, Sperrmüll, Altglas, Problemstoff, Grünschnitt) is
    # classified by the shared vocabulary.
    transform = ICSTransformer(
        clean=_clean,
        type_value_map={
            "Gelbe Säcke": wt.RECYCLABLES,
            "Aschetonne": wt.GENERAL_WASTE,
        },
    )
