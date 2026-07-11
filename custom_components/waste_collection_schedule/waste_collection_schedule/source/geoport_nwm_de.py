"""Landkreis Nordwestmecklenburg (geoport-nwm.de).

Demonstrates: the "year-in-URL, fan out across several per-waste-type ICS
files and merge" shape. There is no dedicated retriever for this yet (a
static ``HttpGetRetriever`` only ever returns one response), so the extra
fetches are done inside a custom ``parse`` override using ``self.session``,
following the documented "parser does a follow-up fetch" pattern. ``retrieve``
still uses the declarative ``HttpGetRetriever`` for the one, always-present
calendar (the district's main "Restmülltonne"-style feed); ``parse`` adds the
optional per-waste-type feeds (paper, hazardous-waste collection, ...) on
top, tolerating the ones that 404 for a given district/year.

Preserves the original's date-window quirk: in December the current and the
following year are both queried (the provider publishes next year's calendar
early); outside December only the current year is used, and a 404 on the
*main* feed still propagates (matching the legacy behaviour observed live for
the "Seefeld" test case, which is not query-year-sensitive).
"""

import datetime
import urllib.parse
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer

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

    TEST_CASES: ClassVar[dict] = {
        "Rüting": {"district": "Rüting"},
        "Grevenstein u. ...": {"district": "Grevenstein u. Ausbau"},
        "Seefeld": {"district": "Seefeld/ Testorf- Steinfort"},
        "1100l": {"district": "Groß Stieten (1.100 l Behälter)"},
        "kl. Bünsdorf": {"district": "Klein Bünsdorf"},
    }

    PARAMS = (district("district"),)

    retrieve = HttpGetRetriever(
        url=lambda district, **_: _API_URL.format(
            year=datetime.date.today().year, arg=_convert_to_arg(district)[0]
        )
    )

    def parse(self, response, source=None):
        district_arg = self.params["district"]
        args = _convert_to_arg(district_arg)
        today = datetime.date.today()
        years = [today.year, today.year + 1] if today.month == 12 else [today.year]

        entries: list = []
        for i, year in enumerate(years):
            if i == 0:
                # Already fetched by `retrieve`; a failure here is real (no
                # calendar at all for this district) so it is left to propagate.
                entries.extend(ICS().convert(response.text))
            else:
                try:
                    r = self.session.get(_API_URL.format(year=year, arg=args[0]))
                    r.raise_for_status()
                    entries.extend(ICS().convert(r.text))
                except Exception:
                    pass

            for prefix in _EXTRA_PREFIXES:
                for arg in args:
                    try:
                        r = self.session.get(
                            _API_URL.format(year=year, arg=f"{prefix}_{arg}")
                        )
                        r.raise_for_status()
                        entries.extend(ICS().convert(r.text))
                    except Exception:
                        pass

        return entries

    transform = ICSTransformer()

    def __init__(self, district: str):
        super().__init__(district=district)
