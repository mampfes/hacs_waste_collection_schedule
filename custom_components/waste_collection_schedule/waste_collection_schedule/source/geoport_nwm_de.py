"""Landkreis Nordwestmecklenburg (geoport-nwm.de).

Demonstrates: the "year-in-URL, fan out across several per-waste-type ICS
files and merge" shape, which is ``IcsYearRetriever`` with ``optional_urls``.
The district's own calendar is required; the four per-contractor feeds
published alongside it exist only where that contractor collects, so they are
best effort and a 404 simply means "not here".

Preserves the original's date-window quirk: in December the current and the
following year are both queried (the provider publishes next year's calendar
early). ``require_lookahead=False`` keeps that extra year best effort, so
December still works before next year's files appear.

Also fixes a latent bug surfaced by converting this source: the district-name
transliteration is ambiguous for names with a dash ("Seefeld/ Testorf-
Steinfort"), so ``_convert_to_arg`` computes two candidate spellings. The
legacy ``fetch_year`` only ever tried the first for the *main* calendar (only
the optional extra-prefix feeds tried both). For "Seefeld" that first spelling
404s live; the second succeeds. The legacy source has therefore always failed
for this TEST_CASE outside December. Here the second spelling is the
retriever's ``fallback_url``, so the main calendar tries both too.
"""

import urllib.parse
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsYearRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import HAZARDOUS, ORGANIC, RECYCLABLES

_API_URL = "https://www.geoport-nwm.de/nwm-download/Abfuhrtermine/ICS/{year}/{arg}.ics"

# Extra per-waste-type feeds published alongside the main district calendar.
_EXTRA_PREFIXES = (
    "Schadstoffmobil",
    "Papiertonne_GER",
    "Papiertonne_Gollan",
    "Papiertonne_Veolia",
)


def _convert_to_arg(district: str) -> list[str]:
    d = district
    d = d.replace("(1.100 l Behälter)", "1100_l")
    d = d.replace("ü", "ue")
    d = d.replace("ö", "oe")
    d = d.replace("ä", "ae")
    d = d.replace("ß", "ss")
    d = d.replace("/", "")
    d = d.replace(".", "")
    d = d.replace(" ", "_")
    arg = urllib.parse.quote(f"Ortsteil_{d}")
    if (
        "-_" in arg
    ):  # inconsistent provider formatting, e.g. "Seefeld/ Testorf- Steinfort"
        return [arg, arg.replace("-_", "-")]
    return [arg]


def _main_url(year: int, district: str, **_) -> str:
    """The district's own calendar, at the first candidate spelling."""
    return _API_URL.format(year=year, arg=_convert_to_arg(district)[0])


def _alternate_url(year: int, district: str, **_) -> str:
    """The same calendar at the other candidate spelling, where there is one."""
    return _API_URL.format(year=year, arg=_convert_to_arg(district)[-1])


def _contractor_urls(year: int, district: str, **_) -> list[str]:
    """Every per-contractor feed, at every candidate spelling."""
    return [
        _API_URL.format(year=year, arg=f"{prefix}_{arg}")
        for prefix in _EXTRA_PREFIXES
        for arg in _convert_to_arg(district)
    ]


@final
class Source(BaseSource):
    TITLE = "Landkreis Nordwestmecklenburg"
    DESCRIPTION = "Source for Landkreis Nordwestmecklenburg."
    URL = "https://www.geoport-nwm.de"
    COUNTRY = "de"

    WASTE_TYPES: ClassVar[list] = [
        HAZARDOUS,
        ORGANIC,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rüting": {"district": "Rüting"},
        "Grevenstein u. ...": {"district": "Grevenstein u. Ausbau"},
        "Seefeld": {"district": "Seefeld/ Testorf- Steinfort"},
        "1100l": {"district": "Groß Stieten (1.100 l Behälter)"},
        "kl. Bünsdorf": {"district": "Klein Bünsdorf"},
    }

    PARAMS = (district("district"),)

    retrieve = IcsYearRetriever(
        url=_main_url,
        fallback_url=_alternate_url,
        optional_urls=_contractor_urls,
        # The provider publishes next year's calendar during December; before
        # it appears, the current year on its own is still the right answer.
        require_lookahead=False,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer()

    def __init__(self, district: str):
        super().__init__(district=district)
