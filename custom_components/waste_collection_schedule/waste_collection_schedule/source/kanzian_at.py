import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import RECYCLABLES

_BASE_URL = "https://www.kanzian.at"

# Kanzian suffixes Hausmüll/Biomüll with the collection day and frequency
# (e.g. "Hausmüll montags 2-wöchentlich", "Biomüll Saison wöchentlich"), which
# is not a fixed, enumerable set a type_value_map could exhaustively list.
# Stripping the variable day/frequency suffix first lets the base label
# (Hausmüll, Biomüll) resolve against the shared vocabulary.
_DAY_FREQ_SUFFIX_RE = re.compile(
    r"\s*(?:montags|dienstags|mittwochs|donnerstags|freitags|samstags|sonntags)?"
    r"\s*(?:saison\s+)?(?:\d+-)?wöchentlich\s*$",
    re.IGNORECASE,
)


def _clean(label: str) -> str:
    return _DAY_FREQ_SUFFIX_RE.sub("", label.strip()).strip()


@final
class Source(BaseSource):
    TITLE = "St. Kanzian am Klopeiner See"
    DESCRIPTION = "Source for St. Kanzian am Klopeiner See, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "St. Kanzian": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "detailonr": "225258384",
            "menuonr": "225275269",
            "typ": "225258384",
        },
    )
    parse = RiSKommunalParser()

    # After the day/frequency suffix is stripped, only the combined "Leicht-
    # und Metallverpackungen" label needs an explicit entry; every other
    # cleaned label (Hausmüll, Restmüll, Biomüll, Bioabfall, Papier,
    # Altpapier, Leichtverpackungen, Gelber Sack, Gelbe Tonne, Sperrmüll,
    # Altglas, Problemstoff) is classified by the shared vocabulary.
    transform = ICSTransformer(
        clean=_clean,
        type_value_map={
            "Leicht- und Metallverpackungen": RECYCLABLES,
        },
    )
