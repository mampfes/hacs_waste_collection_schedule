"""Die NÖ Umweltverbände (umweltverbaende.at).

Demonstrates: a multi-district platform whose districts publish their schedule in
different ways (old HTML pages, ICS links, a WordPress ajax form). The probing and
the reading of each variant live in ``service/Umweltverbaende.py``; the source
declares its districts as ``REGIONS``, its parameters and the label map.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    dropdown,
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Umweltverbaende import (
    DISTRICTS,
    UmweltverbaendeParser,
    UmweltverbaendeRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_VARIANT = re.compile(
    r"(?:\s+(?:WHA|EPH|MPH|\d+x|\d+-wöchentlich)|-\d+x)$", re.IGNORECASE
)

_TYPE_MAP = {
    "asz": wt.OTHER,  # recycling centre opening hours
    "asche": wt.OTHER,
    "christbaumabholung": wt.GARDEN_WASTE,
    "restmuell": wt.GENERAL_WASTE,
    "gelber sack/tonne": wt.RECYCLABLES,
    "gt": wt.RECYCLABLES,
    "pap": wt.PAPER,
    "rm": wt.GENERAL_WASTE,
}


def _clean(label: str) -> str:
    """The waste type of a district's label: the ICS prefix, the container variant
    (``WHA``, ``EPH``, ``18x``, ``2-wöchentlich``) and the recycling-centre hours
    dropped, so ``Restmüll EPH`` and ``Abholung Restmuell`` read as the type."""
    text = label.strip().removeprefix("Abholung ")
    if text.startswith("ASZ"):
        return "ASZ"
    previous = None
    while previous != text:
        previous = text
        text = _VARIANT.sub("", text).strip()
    return text


@final
class Source(BaseSource):
    TITLE = "Die NÖ Umweltverbände"
    DESCRIPTION = (
        "Consolidated waste collection provider for several districts in Lower Austria"
    )
    URL = "https://www.umweltverbaende.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    REGIONS = tuple(
        region(title, url=f"https://{key}.umweltverbaende.at/", district=key)
        for key, title in DISTRICTS.items()
    )

    TEST_CASES: ClassVar[dict] = {
        "Baden": {
            "district": "baden",
            "municipal": "Hernstein",
            "calendar": "ICS Hernstein",
        },
        "Baden - Berndorf Abfuhrbereich II": {
            "district": "baden",
            "municipal": "Berndorf",
            "calendar": "Abfuhrbereich II",
        },  # regression test for issue #4675: Roman numeral collision (II vs III)
        "Gmünd": {"district": "gmuend", "municipal": "Weitra"},
        "Gänserndorf": {"district": "gaenserndorf", "municipal": "Auersthal"},
        "Gänserndorf-New": {
            "district": "gaenserndorf",
            "municipal": "Deutsch-Wagram",
            "street": "Johann Nestroy-Gasse",
            "hnr": "63",
        },
        "Hollabrunn": {
            "district": "hollabrunn",
            "municipal": "Retz",
            "town": "Obernalb",
            "street": "Zum weissen Engel",
        },
        "Hollabrunn - Zellerndorf": {
            "district": "hollabrunn",
            "municipal": "Zellerndorf",
        },  # regression test for #4909: a zone with a fraktion but no "dates"
        "Horn": {"district": "horn", "municipal": "Japons", "town": "Japons"},
        "Korneuburg": {
            "district": "korneuburg",
            "municipal": "Bisamberg",
            "calendar": "Bisamberg B",
            "calendar_title_separator": ",",
            "calendar_splitter": ":",
        },
        "Korneuburg - Enzersfeld": {
            "district": "korneuburg",
            "municipal": "Enzersfeld",
        },  # regression test for #7428: flat ICS list scoped by municipal
        "Krems - Langenlois Land": {
            "district": "krems",
            "municipal": "Langenlois Land",
            "calendar": "Gobelsburg, Mittelberg, Reith, Schiltern, Zöbing",
        },
        "Laa/Thaya": {"district": "laa", "municipal": "Staatz", "town": "kautendorf"},
        "Mödling": {
            "district": "moedling",
            "municipal": "Wienerwald",
            "town": "Gruberau",
        },  # regression test for issue #7476
        "Melk": {"district": "melk", "municipal": "Schollach"},
        "Mistelbach": {"district": "mistelbach", "municipal": "Falkenstein"},
        "St. Pölten": {"district": "stpoeltenland", "municipal": "Pyhra"},
        "Waidhofen/Thaya": {"district": "waidhofen", "municipal": "Kautzen"},
        "Zwettl": {"district": "zwettl", "municipal": "Martinsberg"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your district (the subdomain of its `umweltverbaende.at` site) "
            "and municipality. The district sites come in two kinds: an old one "
            "(light blue header, green buttons) and a new one (dark blue header). "
            "Old site: if your municipality lists several collection calendars "
            "(streets or Rayons), set `calendar` to the name as spelt on the "
            "Abholtermine page below `Kalenderansicht`; rarely, "
            "`calendar_title_separator` (default `:`) separates the calendar title "
            "from the waste type and `calendar_splitter` separates several types "
            "listed in one line. New site: `town`, `plz`, `street`, `hnr` and "
            "`addition` are rarely needed, set them only when you get an error "
            "without them; the error lists the valid values. Scheibbs publishes "
            "PDF files only and Stadt Krems has its own ICS source."
        ),
        "de": (
            "Wählen Sie Ihren Verband (die Subdomain seiner `umweltverbaende.at`-"
            "Seite) und Ihre Gemeinde. Es gibt zwei Arten von Seiten: eine alte "
            "(hellblaue Kopfzeile, grüne Schaltflächen) und eine neue (dunkelblaue "
            "Kopfzeile). Alte Seite: Werden für Ihre Gemeinde mehrere "
            "Abfallkalender angezeigt (Straßen oder Rayons), tragen Sie in "
            "`calendar` den Namen so ein, wie er auf der Abholtermine-Seite unter "
            "`Kalenderansicht` steht; selten nötig: `calendar_title_separator` "
            "(Standard `:`) trennt Kalendertitel und Abfallart, "
            "`calendar_splitter` trennt mehrere Abfallarten einer Zeile. Neue "
            "Seite: `town`, `plz`, `street`, `hnr` und `addition` sind selten "
            "nötig, nur angeben, wenn ohne sie ein Fehler auftritt; die "
            "Fehlermeldung nennt die gültigen Werte. Scheibbs veröffentlicht nur "
            "PDF-Dateien und die Stadt Krems hat eine eigene ICS-Quelle."
        ),
    }

    PARAMS = (
        dropdown("district", list(DISTRICTS), label="District"),
        municipality("municipal"),
        city("town", optional=True),
        text_field("plz", label="Postal code", optional=True),
        street(optional=True),
        house_number("hnr", optional=True),
        text_field("addition", optional=True),
        text_field("calendar", optional=True),
        text_field("calendar_title_separator", default=":"),
        text_field("calendar_splitter", optional=True),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    retrieve = UmweltverbaendeRetriever()
    parse = UmweltverbaendeParser()
    transform = ICSTransformer(
        type_value_map=_TYPE_MAP, clean=_clean, carry_raw_label=True
    )
