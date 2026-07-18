from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.AbfallnaviDe import (
    AbfallnaviParser,
    AbfallnaviRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Waste-type names come back as open-ended German fraktion strings that vary by
# municipality, so this source declares NO per-source type map: the shared
# multilingual resolver (waste_types.resolve) classifies the standard German
# labels, and anything it doesn't recognise is preserved verbatim rather than
# collapsed to OTHER.


# The provider registry for this one structure: each entry becomes a Region
# (a discoverable listing with its regio iT service id pre-filled). New
# providers are added here, in the source that owns them.
_PROVIDERS = [
    {
        "title": "Stadt Aachen",
        "url": "https://www.aachen.de",
        "service_id": "aachen",
    },
    {
        "title": "Abfallwirtschaft Stadt Nürnberg",
        "url": "https://www.nuernberg.de/",
        "service_id": "nuernberg",
    },
    {
        "title": "Abfallwirtschaftsbetrieb Bergisch Gladbach",
        "url": "https://www.bergischgladbach.de/",
        "service_id": "aw-bgl2",
    },
    {
        "title": "AWA Entsorgungs GmbH",
        "url": "https://www.awa-gmbh.de/",
        "service_id": "zew2",
    },
    {
        "title": "AWG Kreis Warendorf",
        "url": "https://www.awg-waf.de/",
        "service_id": "krwaf",
    },
    {
        "title": "Bergischer Abfallwirtschaftverbund",
        "url": "https://www.bavweb.de/",
        "service_id": "bav",
    },
    {
        "title": "Kreis Coesfeld",
        "url": "https://wbc-coesfeld.de/",
        "service_id": "coe",
    },
    {
        "title": "Stadt Cottbus",
        "url": "https://www.cottbus.de/",
        "service_id": "cottbus",
    },
    {
        "title": "Dinslaken",
        "url": "https://www.dinslaken.de/",
        "service_id": "din",
    },
    {
        "title": "Stadt Dorsten",
        "url": "https://www.ebd-dorsten.de/",
        "service_id": "dorsten",
    },
    {
        "title": "EGW Westmünsterland",
        "url": "https://www.egw.de/",
        "service_id": "wml2",
    },
    {
        "title": "Kreis Gütersloh GEG",
        "url": "https://www.geg-gt.de/",
        "service_id": "krwaf",
    },
    {
        "title": "Halver",
        "url": "https://www.halver.de/",
        "service_id": "hlv",
    },
    {
        "title": "Kreis Heinsberg",
        "url": "https://www.kreis-heinsberg.de/",
        "service_id": "krhs",
    },
    {
        "title": "Kronberg im Taunus",
        "url": "https://www.kronberg.de/",
        "service_id": "kronberg",
    },
    {
        "title": "MHEG Mülheim an der Ruhr",
        "url": "https://www.mheg.de/",
        "service_id": "muelheim",
    },
    {
        "title": "Stadt Norderstedt",
        "url": "https://www.betriebsamt-norderstedt.de/",
        "service_id": "nds",
    },
    {
        "title": "Kreis Pinneberg",
        "url": "https://www.kreis-pinneberg.de/",
        "service_id": "pi",
    },
    {
        "title": "Gemeinde Roetgen",
        "url": "https://www.roetgen.de/",
        "service_id": "roe",
    },
    {
        "title": "Stadt Solingen",
        "url": "https://www.solingen.de/",
        "service_id": "solingen",
    },
    {
        "title": "STL Lüdenscheid",
        "url": "https://www.stl-luedenscheid.de/",
        "service_id": "stl",
    },
    {
        "title": "GWA - Kreis Unna mbH",
        "url": "https://www.gwa-online.de/",
        "service_id": "unna",
    },
    {
        "title": "Kreis Viersen",
        "url": "https://www.kreis-viersen.de/",
        "service_id": "viersen",
    },
    {
        "title": "WBO Wirtschaftsbetriebe Oberhausen",
        "url": "https://www.wbo-online.de/",
        "service_id": "oberhausen",
    },
    {
        "title": "ZEW Zweckverband Entsorgungsregion West",
        "url": "https://zew-entsorgung.de/",
        "service_id": "zew2",
    },
    #    {
    #        "title": "'Stadt Straelen",
    #        "url": "https://www.straelen.de/",
    #        "service_id": "straelen",
    #    },
    {
        "title": "Stadt Cuxhaven",
        "url": "https://www.cuxhaven.de/",
        "service_id": "cux",
    },
    {
        "title": "Stadt Frankenthal",
        "url": "https://www.frankenthal.de/",
        "service_id": "frankenthal",
    },
    {
        "title": "Abfallwirtschaftsverband Lippe",
        "url": "https://www.abfall-lippe.de/",
        "service_id": "awvlippe",
    },
    {
        "title": "Gemeinde Kranenburg",
        "url": "https://www.kranenburg.de/",
        "service_id": "kranenburg",
    },
    {
        "title": "Stadt Porta Westfalica",
        "url": "https://www.portawestfalica.de/",
        "service_id": "portawestfalica",
    },
]


def _regions() -> list[Region]:
    return [
        region(s["title"], url=s["url"], service=s["service_id"]) for s in _PROVIDERS
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
    # full list is derived from the source's own provider registry at load time.
    REGIONS = _regions

    TEST_CASES: ClassVar[dict] = {
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
        "nds Norderstedt Friedrichsgaber Weg (house number range as street)": {
            "service": "nds",
            "ort": "Norderstedt",
            "strasse": "Friedrichsgaber Weg 1 - 57",
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

    PARAMS = (
        text_field("service", "Service"),
        text_field("ort", "Ort"),
        text_field("strasse", "Straße", optional=True),
        text_field("hausnummer", "Hausnummer", optional=True),
    )

    HOWTO: ClassVar[dict] = {
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
