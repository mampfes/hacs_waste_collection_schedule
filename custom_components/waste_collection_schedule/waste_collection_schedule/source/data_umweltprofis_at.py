"""Umweltprofis (umweltprofis.at).

Demonstrates: a single provider exposing two unrelated static GET feeds under
one source -- a deprecated personal ICS export (``url``) and its replacement, a
personal XML export (``xmlurl``) -- selected via ``alternatives()`` so the
config flow accepts exactly one. ``HttpGetRetriever`` fetches whichever URL was
given, and ``ByBodyPrefix`` picks the parser from the body that came back:
``IcsFeedsParser`` for the iCalendar export, ``XmlDateListParser`` for the
other. Both produce the same ``(date, summary)`` shape ``ICSTransformer``
expects.

The ICS branch undoes a provider quirk first, through ``IcsFeedsParser``'s
``unwrap`` hook: this provider spaces out the ``REFRESH-INTERVAL`` property so
that no ICS library accepts it as written.

No ``type_value_map``: the legacy source never mapped a type either, and the
shared multilingual resolver already recognises most of this provider's labels,
so nothing is lost by not hand-mapping the rest.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, text_field
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import IcsFeedsParser
from waste_collection_schedule.transformers import ICSTransformer

_REFRESH_INTERVAL_FIX = ("REFRESH - INTERVAL; VALUE = ", "REFRESH-INTERVAL;VALUE=")


def _resolve_url(
    url: "str | None" = None, xmlurl: "str | None" = None, **_: object
) -> str:
    resolved = url or xmlurl
    if not resolved:
        raise SourceArgumentRequired("url", "either url or xmlurl must be provided")
    return resolved


def _repair_refresh_interval(text: str) -> str:
    """Rejoin the ``REFRESH-INTERVAL`` property this provider spaces out."""
    for broken, fixed in (_REFRESH_INTERVAL_FIX,):
        text = text.replace(broken, fixed)
    return text


@final
class Source(BaseSource):
    TITLE = "Umweltprofis"
    DESCRIPTION = "Source for Umweltprofis"
    URL = "https://www.umweltprofis.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Ebensee": {
            "url": "https://data.umweltprofis.at/OpenData/AppointmentService/AppointmentService.asmx/GetIcalWastePickupCalendar?key=KXX_K0bIXDdk0NrTkk3xWqLM9-bsNgIVBE6FMXDObTqxmp9S39nIqwhf9LTIAX9shrlpfCYU7TG_8pS9NjkAJnM_ruQ1SYm3V9YXVRfLRws1"
        },
        "Rohrbach": {
            "xmlurl": "https://data.umweltprofis.at/opendata/AppointmentService/AppointmentService.asmx/GetTermineForLocationSecured?Key=TEMPKeyabvvMKVCic0cMcmsTEMPKey&StreetNr=118213&HouseNr=Alle&intervall=Alle"
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "You need to generate your personal XML link before you can start "
            "using this source. Go to "
            "https://data.umweltprofis.at/opendata/AppointmentService/index.aspx "
            "and fill out the form. At the end, step 6 gives you a link to an "
            "XML file. Copy this link and use it as the XML URL."
        ),
        "de": (
            "Sie müssen zuerst Ihren persönlichen XML-Link generieren, bevor Sie "
            "diese Quelle verwenden können. Gehen Sie zu "
            "https://data.umweltprofis.at/opendata/AppointmentService/index.aspx "
            "und füllen Sie das Formular aus. Am Ende von Schritt 6 erhalten Sie "
            "einen Link zu einer XML-Datei. Kopieren Sie diesen Link und "
            "verwenden Sie ihn als XML-URL."
        ),
    }

    PARAMS = (
        alternatives(
            [text_field("url", "URL (Deprecated do not use)")],
            [text_field("xmlurl", "XML URL")],
        ),
    )

    retrieve = HttpGetRetriever(url=_resolve_url)

    parse = parsers.ByBodyPrefix(
        {
            "BEGIN:VCALENDAR": IcsFeedsParser(
                parsers.IcsParser(), unwrap=_repair_refresh_interval
            )
        },
        default=parsers.XmlDateListParser("AppointmentEntry", "Datum", "WasteType"),
    )

    # No WASTE_TYPES. A bare pass-through transformer has no
    # type_value_map, so every label this feed sends is classified by the
    # shared multilingual vocabulary, which cannot be enumerated
    # statically; and with no cassette yet (#7095) the produced set
    # cannot be derived by replay either. An empty declaration is the
    # honest one, and it only narrows a config-flow dropdown offer
    # (#7028). Declare the real vocabulary once this source is recorded.
    transform = ICSTransformer()
