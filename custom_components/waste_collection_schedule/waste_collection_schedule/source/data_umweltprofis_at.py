"""Umweltprofis (umweltprofis.at).

Demonstrates: a single provider exposing two unrelated static GET feeds under
one source -- a deprecated personal ICS export (``url``) and its replacement,
a personal XML export (``xmlurl``) -- selected via ``alternatives()`` so the
config flow accepts exactly one. ``retrieve`` fetches whichever URL was
given; ``parse`` sniffs the body (an ICS export starts with
``BEGIN:VCALENDAR``, everything else here is the XML export) and hands off to
the matching parser: the plain ``ICS()`` service class (after undoing a
provider quirk in the ``REFRESH-INTERVAL`` property no ICS library accepts as
written) for the ICS branch, or a small XML walk for the other. Both branches
produce the same ``(date, summary)`` shape ``ICSTransformer`` expects. No
``type_value_map``: the legacy source never mapped a type either, and the
shared multilingual resolver already recognises most of this provider's
labels, so nothing is lost by not hand-mapping the rest.
"""

import datetime
from typing import ClassVar, final
from xml.dom.minidom import parseString

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer

_REFRESH_INTERVAL_FIX = ("REFRESH - INTERVAL; VALUE = ", "REFRESH-INTERVAL;VALUE=")


def _element_text(element) -> str:
    return "".join(
        node.nodeValue for node in element.childNodes if node.nodeType == node.TEXT_NODE
    )


def _parse_xml(text: str) -> list[tuple[datetime.date, str]]:
    doc = parseString(text)  # nosec B318
    entries = []
    for appointment in doc.getElementsByTagName("AppointmentEntry"):
        date_str = _element_text(appointment.getElementsByTagName("Datum")[0])
        waste_type = _element_text(appointment.getElementsByTagName("WasteType")[0])
        entries.append((datetime.datetime.fromisoformat(date_str).date(), waste_type))
    return entries


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

    retrieve = HttpGetRetriever(url=lambda url=None, xmlurl=None, **_: url or xmlurl)

    def parse(self, response, source=None):
        text = response.text
        if text.lstrip().startswith("BEGIN:VCALENDAR"):
            for broken, fixed in (_REFRESH_INTERVAL_FIX,):
                text = text.replace(broken, fixed)
            return ICS().convert(text)
        return _parse_xml(text)

    transform = ICSTransformer()

    def __init__(self, url: "str | None" = None, xmlurl: "str | None" = None):
        super().__init__(url=url, xmlurl=xmlurl)
