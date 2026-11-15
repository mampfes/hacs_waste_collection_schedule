"""Gemeindewerke Pfäffikon ZH (gwpzh.ch), Switzerland.

The provider publishes eight public Google Calendars on
https://www.gwpzh.ch/kalender: municipality-wide Altpapier, Karton and
Sonderabfall / Bring- und Holtag calendars, plus zone-specific calendars for
Kehricht/Sperrgut and Grüngut. Kehricht/Sperrgut uses one calendar for
Sammelkreis 1 and a shared calendar for Sammelkreis 2 and 3; Grüngut has a
calendar per Sammelkreis. There is no street-to-zone lookup; residents pick
their Sammelkreis from the area descriptions on the calendar page.
"""

from __future__ import annotations

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import FanOutRetriever
from waste_collection_schedule.transformers import ICSTransformer

_ICS = (
    "https://calendar.google.com/calendar/ical/"
    "{}%40group.calendar.google.com/public/basic.ics"
)

# Municipality-wide calendars, fetched for every Sammelkreis.
_SHARED = [
    _ICS.format("np0p9nd9lm0ajoocog3fre4uug"),  # Altpapier
    _ICS.format("0hi489a7pmtg44kcpjnhvae738"),  # Karton
    _ICS.format("a0g1vdic9uog7k029itm1nbkl0"),  # Sonderabfall / Bring- und Holtag
]

# Zone-specific Kehricht/Sperrgut and Grüngut calendars. Sammelkreis 2 and 3
# share the Kehricht/Sperrgut feed.
_ZONE_CALENDARS = {
    "Sammelkreis 1": [
        _ICS.format("v3mhfethgall6gb22kc4dpmhj4"),  # Kehricht/Sperrgut SK1
        _ICS.format("fr7c1ca4vsv2uef61aeje9hmc4"),  # Grüngut SK1
    ],
    "Sammelkreis 2": [
        _ICS.format("lte7p0ha17dm28c2otf102vto4"),  # Kehricht/Sperrgut SK2+3
        _ICS.format("j2uktmlfj2o4q68ofvv2uci0lc"),  # Grüngut SK2
    ],
    "Sammelkreis 3": [
        _ICS.format("lte7p0ha17dm28c2otf102vto4"),  # Kehricht/Sperrgut SK2+3
        _ICS.format("0cq634grsiqsllh499j5ttshac"),  # Grüngut SK3
    ],
}

ZONES = list(_ZONE_CALENDARS)

_SAMMELKREIS_SUFFIX = re.compile(r"\s*[-–]\s*Sammelkreis\s*.*$", re.IGNORECASE)
_TRAILING_PARENS = re.compile(r"\s*\([^)]*\)\s*$")


def _calendar_urls(source: BaseSource, _context: object) -> list[str]:
    """Shared calendars plus the Kehricht and Grüngut feeds for the zone."""
    zone = source.params["zone"]
    calendars = _ZONE_CALENDARS.get(zone)
    if calendars is None:
        raise SourceArgumentNotFoundWithSuggestions("zone", zone, ZONES)
    return [*_SHARED, *calendars]


def _clean_summary(summary: str) -> str:
    """Strip the Sammelkreis suffix and the club name in parentheses."""
    summary = _SAMMELKREIS_SUFFIX.sub("", summary)
    return _TRAILING_PARENS.sub("", summary).strip()


@final
class Source(BaseSource):
    TITLE = "Gemeindewerke Pfäffikon ZH"
    DESCRIPTION = "Source for Gemeindewerke Pfäffikon ZH, Switzerland."
    URL = "https://www.gwpzh.ch/kalender"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Wallikerstrasse 81, Wallikon (Sammelkreis 1)": {"zone": "Sammelkreis 1"},
        "Sammelkreis 2": {"zone": "Sammelkreis 2"},
        "Sammelkreis 3": {"zone": "Sammelkreis 3"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown Sammelkreis": {"zone": "Sammelkreis 4"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Select your Sammelkreis (collection district) on the waste calendar "
            "at https://www.gwpzh.ch/kalender. The districts are described there: "
            "Sammelkreis 1 is north of the railway line up to Hochstrasse 199, "
            "including Irgenhausen, Neuhof, Oberwil, Bussenhausen, Steinacker, "
            "Berg, Wallikon, Humbel, Hermatswil, Ravensbüel, Rick, Seiler, Schür "
            "and Sulzberg. Sammelkreis 2 is south of the railway line from "
            "Bahnhofstrasse/Hochstrasse/Pilatusstrasse towards Wetzikon, plus "
            "from Hochstrasse 200, Tumbelen, Bächliacher, Sitzbühl, Lierennagel, "
            "Unter- and Oberbalm and Auslikon. Sammelkreis 3 is south of the "
            "railway line from Bahnhofstrasse/Hochstrasse/Pilatusstrasse towards "
            "Fehraltorf, including Frohwies, Matten, Im Spitz, Büel, the Schanz "
            "and Witzberg industrial areas, Faichrüti and Ruetschberg. "
            "Altpapier, Karton and Sonderabfall are municipality-wide. "
            "The example address Wallikerstrasse 81 (Wallikon) is Sammelkreis 1."
        ),
        "de": (
            "Wählen Sie Ihren Sammelkreis auf dem Abfallkalender unter "
            "https://www.gwpzh.ch/kalender. Die Gebiete sind dort beschrieben: "
            "Sammelkreis 1 liegt nördlich der Bahnlinie bis Hochstrasse 199, "
            "inkl. Irgenhausen, Neuhof, Oberwil, Bussenhausen, Steinacker, Berg, "
            "Wallikon, Humbel, Hermatswil, Ravensbüel, Rick, Seiler, Schür und "
            "Sulzberg. Sammelkreis 2 liegt südlich der Bahnlinie ab "
            "Bahnhofstrasse/Hochstrasse/Pilatusstrasse in Richtung Wetzikon sowie "
            "ab Hochstrasse 200, Tumbelen, Bächliacher, Sitzbühl, Lierennagel, "
            "Unter- und Oberbalm und Auslikon. Sammelkreis 3 liegt südlich der "
            "Bahnlinie ab Bahnhofstrasse/Hochstrasse/Pilatusstrasse in Richtung "
            "Fehraltorf, inkl. Frohwies, Matten, Im Spitz, Büel, Industriegebiet "
            "Schanz und Witzberg, Faichrüti und Ruetschberg. Altpapier, Karton "
            "und Sonderabfall gelten gemeindeweit. Die Beispieladresse "
            "Wallikerstrasse 81 (Wallikon) gehört zu Sammelkreis 1."
        ),
    }

    PARAMS = (dropdown("zone", ZONES),)

    retrieve = FanOutRetriever(targets=_calendar_urls)
    parse = parsers.EachResponse(parsers.IcsParser())
    transform = ICSTransformer(
        clean=_clean_summary,
        type_value_map={
            "Kehricht/Sperrgut": wt.GENERAL_WASTE,
            "Kehricht": wt.GENERAL_WASTE,
            "Grüngut": wt.GARDEN_WASTE,
            "Häckseldienst": wt.GARDEN_WASTE,
            "Sonderabfallmobil": wt.HAZARDOUS,
            "Bring- und Holtag": wt.BULKY_WASTE,
        },
    )
