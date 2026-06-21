from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.regions import Region, region
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


def _regions() -> list[Region]:
    return [
        region(s["title"], url=s["url"], service=s["service_id"])
        for s in SERVICE_DOMAINS
    ]


@final
class Source(BaseSource):
    TITLE = "AbfallNavi (RegioIT.de)"
    DESCRIPTION = (
        "Source for AbfallNavi waste collection. "
        "AbfallNavi is a brand name of regioit.de."
    )
    URL = "https://www.regioit.de"
    COUNTRY = "de"

    # One structure (regioit.de AbfallNavi) covering many municipalities; the
    # full list is derived from the shared SERVICE_DOMAINS registry at load time.
    REGIONS = _regions

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
        "Pinneberg Kummerfeld, Dorfstraße": {
            "service": "pi",
            "ort": "Kummerfeld",
            "strasse": "Dorfstraße",
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

    PARAMS = [
        text_field("service", "Service"),
        text_field("ort", "Ort"),
        text_field("strasse", "Straße", optional=True),
        text_field("hausnummer", "Hausnummer", optional=True),
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
    transform = ICSTransformer()  # types resolved via the shared vocabulary

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
