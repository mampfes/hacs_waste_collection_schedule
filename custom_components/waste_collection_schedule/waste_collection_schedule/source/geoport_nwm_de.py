"""Landkreis Nordwestmecklenburg (geoport-nwm.de).

Demonstrates: the "year-in-URL, fan out across several per-waste-type ICS
files and merge" shape. There is no dedicated retriever for this yet, so the
whole fetch (main calendar plus the optional per-waste-type feeds) is done in
a ``retrieve`` override using ``self.session``, tolerating the individual
feeds that 404 for a given district/year/name-variant.

Preserves the original's date-window quirk: in December the current and the
following year are both queried (the provider publishes next year's calendar
early); outside December only the current year is used.

Also fixes a latent bug surfaced by converting this source: the district-name
transliteration is ambiguous for names with a dash ("Seefeld/ Testorf-
Steinfort"), so ``_convert_to_arg`` already computes two candidate spellings —
but the legacy ``fetch_year`` only ever tried the first for the *main*
calendar (only the optional extra-prefix feeds tried both). For "Seefeld"
that first spelling 404s live; the second succeeds. The legacy source has
therefore always failed for this TEST_CASE outside December. This version
tries every candidate spelling for the main calendar too, which resolves it.
"""

import datetime
import urllib.parse
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.service.ICS import ICS
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

    def retrieve(self, source):
        district_arg = self.params["district"]
        args = _convert_to_arg(district_arg)
        today = datetime.date.today()
        years = [today.year, today.year + 1] if today.month == 12 else [today.year]

        texts: list[str] = []
        for i, year in enumerate(years):
            main_text = None
            for arg in args:
                try:
                    r = self.session.get(_API_URL.format(year=year, arg=arg))
                    r.raise_for_status()
                    main_text = r.text
                    break
                except Exception:
                    continue
            if main_text is not None:
                texts.append(main_text)
            elif i == 0:
                # No spelling worked for the required year: nothing to show.
                raise ValueError(
                    f"no calendar found for district {district_arg!r} ({year})"
                )

            for prefix in _EXTRA_PREFIXES:
                for arg in args:
                    try:
                        r = self.session.get(
                            _API_URL.format(year=year, arg=f"{prefix}_{arg}")
                        )
                        r.raise_for_status()
                        texts.append(r.text)
                    except Exception:
                        pass

        return texts

    def parse(self, response, source=None):
        entries: list = []
        for text in response:
            entries.extend(ICS().convert(text))
        return entries

    transform = ICSTransformer()

    def __init__(self, district: str):
        super().__init__(district=district)
