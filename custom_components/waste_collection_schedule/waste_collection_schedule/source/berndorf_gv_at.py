from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

_BASE_URL = "https://www.berndorf.gv.at"

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

    TEST_CASES: ClassVar[dict] = {
        "Berndorf": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "226080602",
        },
    )
    parse = RiSKommunalParser()

    # After the site-name prefix is stripped, only the plural "Gelbe Säcke"
    # and the ash bin (Aschetonne, no canonical equivalent; collected
    # alongside residual waste) need an explicit entry; every other cleaned
    # label (Restmüll, Biotonne, Bioabfall, Biomüll, Altpapier, Papier, Gelber
    # Sack, Gelbe Tonne, Sperrmüll, Altglas, Problemstoff, Grünschnitt) is
    # classified by the shared vocabulary. The calendar also carries a handful
    # of unrelated local-business notices ("Heuriger - ..."), preserved
    # verbatim with no icon, matching the legacy unmapped-label behaviour.
    transform = ICSTransformer(
        clean=_clean,
        type_value_map={
            "Gelbe Säcke": RECYCLABLES,
            "Aschetonne": GENERAL_WASTE,
        },
    )
