from dataclasses import replace

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.AbfallnaviDe import (
    SERVICE_DOMAINS,
    AbfallnaviParser,
    AbfallnaviRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Waste-type names come back as open-ended German fraktion strings that vary by
# municipality, so this source declares NO per-source type map: the shared
# multilingual resolver (waste_types.resolve) classifies the standard German
# labels, and anything it doesn't recognise is preserved verbatim rather than
# collapsed to OTHER.

TITLE = "AbfallNavi (RegioIT.de)"
DESCRIPTION = (
    "Source for AbfallNavi waste collection. AbfallNavi is a brand name of regioit.de."
)
URL = "https://www.regioit.de"


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": s["url"],
            "default_params": {"service": s["service_id"]},
        }
        for s in SERVICE_DOMAINS
    ]


TEST_CASES = {
    "Aachen, Abteiplatz 7": {
        "service": "aachen",
        "ort": "Aachen",
        "strasse": "Abteiplatz",
        "hausnummer": "7",
    },
    "Lindlar, Aggerweg": {
        "service": "bav",
        "ort": "Lindlar",
        "strasse": "Aggerweg",
    },
    "Overath, Hauptstraße": {
        "service": "bav",
        "ort": "Overath",
        "strasse": "Hauptstraße",
    },
    "Roetgen, Am Sportplatz 2": {
        "service": "zew2",
        "ort": "Roetgen",
        "strasse": "Am Sportplatz",
        "hausnummer": "2",
    },
    "nds Norderstedt Adenauerplatz": {
        "service": "nds",
        "ort": "Norderstedt",
        "strasse": "Distelweg",
    },
    "una Bergkamen, Agnes-Miegel-Str.": {
        "service": "unna",
        "ort": "Bergkamen",
        "strasse": "Agnes-Miegel-Str.",
    },
    "Pinneberg Kummerfeld no Street": {
        "service": "pi",
        "ort": "Kummerfeld",
        "strasse": "alle Straßen",
    },
    "Cuxhaven": {
        "service": "cux",
        "ort": "Cuxhaven",
        "strasse": "Zur Holter Höhe",
    },
    "frankenthal, Am Martinspfad": {
        "service": "frankenthal",
        "ort": "Frankenthal",
        "strasse": "Am Martinspfad",
    },
}


class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = "de"
    TEST_CASES = TEST_CASES

    PARAMS = [
        text_field("service", "Service"),
        text_field("ort", "Ort"),
        replace(text_field("strasse", "Straße"), required=False),
        replace(text_field("hausnummer", "Hausnummer"), required=False),
    ]

    HOWTO = {
        "en": (
            "Pick the 'service' id for your region from the source's list of "
            "municipalities, then enter your town ('ort'), and where required "
            "the street ('strasse') and house number ('hausnummer')."
        ),
        "de": (
            "Wählen Sie die 'service'-Kennung Ihrer Region aus der Liste der "
            "Kommunen, geben Sie dann Ihren Ort an und, falls erforderlich, "
            "die Straße ('strasse') und Hausnummer ('hausnummer')."
        ),
    }

    retrieve = AbfallnaviRetriever(
        service="service",
        city="ort",
        street="strasse",
        house_number="hausnummer",
    )
    parse = AbfallnaviParser()
    transformer = ICSTransformer()  # types resolved via the shared vocabulary

    def __init__(
        self,
        service: str,
        ort: str,
        strasse: str | None = None,
        hausnummer: str | int | None = None,
    ):
        super().__init__(
            service=service,
            ort=ort,
            strasse=strasse,
            hausnummer=(str(hausnummer) if isinstance(hausnummer, int) else hausnummer),
        )
