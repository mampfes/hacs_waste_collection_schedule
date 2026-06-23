from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    area_id,
    city,
    city_id,
    house_number,
    service_id,
    street,
)
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.Jumomind import (
    JumomindParser,
    JumomindRetriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import ALL_TYPES

# Waste-type names come back as open-ended German labels that vary by provider,
# so this source declares NO per-source type map: the transformer resolves the
# standard German labels via the shared multilingual vocabulary
# (waste_types.resolve), and anything it doesn't recognise is preserved verbatim
# rather than collapsed to OTHER.


# The provider registry for this one structure: each entry becomes one or more
# Regions (a discoverable listing with its Jumomind service id pre-filled). New
# providers are added here, in the source that owns them. ``comment`` is an
# optional listing suffix (e.g. the white-label app the provider runs under).
_PROVIDERS = [
    {
        "service_id": "zaw",
        "url": "https://www.zaw-online.de",
        "cities": ["Darmstadt-Dieburg (ZAW)"],
    },
    {
        "service_id": "aoe",
        "url": "https://www.lra-aoe.de",
        "cities": ["Altötting (LK)"],
    },
    {
        "service_id": "lka",
        "url": "https://mkw-grossefehn.de",
        "cities": ["Aurich (MKW)"],
    },
    {
        "service_id": "hom",
        "url": "https://www.bad-homburg.de",
        "cities": ["Bad Homburg vdH"],
    },
    {
        "service_id": "bdg",
        "url": "https://www.kreiswerke-barnim.de/",
        "cities": ["Barnim"],
    },
    {
        "service_id": "hat",
        "url": "https://www.hattersheim.de",
        "cities": ["Hattersheim am Main"],
    },
    {"service_id": "ingol", "url": "https://www.in-kb.de", "cities": ["Ingolstadt"]},
    {
        "service_id": "lue",
        "url": "https://www.luebbecke.de",
        "comment": "Jumomind",
        "cities": ["Lübbecke"],
    },
    {"service_id": "sbm", "url": "https://www.minden.de/", "cities": ["Minden"]},
    {
        "service_id": "ksr",
        "url": "https://www.zbh-ksr.de",
        "cities": ["Recklinghausen"],
    },
    {
        "service_id": "rhe",
        "url": "https://www.rh-entsorgung.de/",
        "comment": "Jumomind",
        "cities": ["Rhein-Hunsrück"],
    },
    {
        "service_id": "udg",
        "url": "https://www.udg-uckermark.de/",
        "cities": ["Uckermark"],
    },
    {
        "service_id": "mymuell",
        "url": "https://www.mymuell.de/",
        "comment": "MyMuell App",
        "cities": [
            "Aschaffenburg",
            "Bad Arolsen",
            "Beverungen",
            "Darmstadt",
            "Esens",
            "Flensburg",
            "Gelnhausen",
            "Glashütten",
            "Grävenwiesbach",
            "Großkrotzenburg",
            "Hainburg",
            "Holtgast",
            "Kamp-Lintfort",
            "Kirchdorf",
            "Landkreis Aschaffenburg",
            "Landkreis Biberach",
            "Landkreis Eichstätt",
            "Landkreis Friesland",
            "Landkreis Leer",
            "Landkreis Mettmann",
            "Landkreis Paderborn",
            "Landkreis Wittmund",
            "Main-Kinzig-Kreis",
            "Mühlheim am Main",
            "Nenndorf",
            "Neumünster",
            "Salzgitter",
            "Schmitten im Taunus",
            "Schöneck",
            "Seligenstadt",
            "Ulm",
            "Usingen",
            "Volkmarsen",
            "Vöhringen",
            "Wegberg",
            "Westerholt",
            "Wilhelmshaven",
        ],
    },
    {
        "service_id": "esn",
        "url": "https://www.neustadt.eu/",
        "cities": ["Neustadt an der Weinstraße"],
    },
    {"service_id": "zac", "url": "https://www.zacelle.de/", "cities": ["Celle"]},
    {
        "service_id": "ben",
        "url": "https://awb.grafschaft-bentheim.de/",
        "cities": ["Landkreis Grafschaft"],
    },
    {
        "service_id": "enwi",
        "url": "https://www.enwi-hz.de/",
        "cities": ["Landkreis Harz"],
    },
    {
        "service_id": "hox",
        "url": "https://abfallservice.kreis-hoexter.de/",
        "cities": ["Höxter"],
    },
    {"service_id": "kbl", "url": "https://www.kbl-langen.de/", "cities": ["Langen"]},
    {
        "service_id": "ros",
        "url": "https://www.rosbach-hessen.de/",
        "cities": ["Rosbach Vor Der Höhe"],
    },
    {
        "service_id": "mkk",
        "url": "https://abfall-mkk.de/",
        "cities": ["Main-Kinzig-Kreis"],
    },
    {
        "service_id": "wol",
        "url": "https://www.alw-wf.de",
        "cities": ["ALW Wolfenbüttel"],
    },
]


def _regions() -> list[Region]:
    regions: list[Region] = []
    for provider in _PROVIDERS:
        comment = f" ({provider['comment']})" if "comment" in provider else ""
        for city_name in provider["cities"]:
            regions.append(
                region(
                    f"{city_name}{comment}",
                    url=provider["url"],
                    service_id=provider["service_id"],
                )
            )
    return regions


# Not @final: rh_entsorgung_de subclasses this for the RHE municipality.
class Source(BaseSource):
    TITLE = "Jumomind"
    DESCRIPTION = "Source for Jumomind.de waste collection."
    URL = "https://www.jumomind.de"
    COUNTRY = "de"
    # The transformer resolves open-ended German labels via the shared vocabulary,
    # so any canonical type may appear.
    WASTE_TYPES = list(ALL_TYPES)

    # One structure (the Jumomind mmapp API) covering many municipalities; the
    # full list is derived from the source's own provider registry at load time.
    REGIONS = _regions

    TEST_CASES = {
        # DEPRECATED
        "ZAW": {"service_id": "zaw", "city_id": 106, "area_id": 94},
        "Bad Homburg, Bahnhofstrasse": {
            "service_id": "hom",
            "city_id": 1,
            "area_id": 411,
        },
        # END DEPRECATED
        "sbm Minden Meißener Str. 6a": {
            "service_id": "sbm",
            "city": "Minden",
            "street": "Meißener Str.",
            "house_number": "6A",
        },
        "Darmstaadt ": {
            "service_id": "mymuell",
            "city": "Darmstadt",
            "street": "Achatweg",
        },
        "zaw Alsbach-Hähnlein Hähnleiner Str.": {
            "service_id": "zaw",
            "city": "Alsbach-Hähnlein",
            "street": "Hähnleiner Str.",
        },
        "ingolstadt": {
            "service_id": "ingol",
            "city": "Ingolstadt",
            "street": "Hauffstr.",
            "house_number": "9 1/2",
        },
        "mymuell only city": {
            "service_id": "mymuell",
            "city": "Bad Wünnenberg-Bleiwäsche",
        },
        "neustadt": {
            "service_id": "esn",
            "city": "Neustadt",
            "street": "Hauberallee (Kernstadt)",
        },
        "Main-Kinzig-Kreis": {
            "service_id": "mkk",
            "city": "Freigericht",
            "street": "Hauptstraße (Altenmittlau)",
        },
        "ALW Wolfenbüttel": {
            "service_id": "wol",
            "city": "Linden",
            "street": "Am Buschkopf",
        },
        "KSR Recklinghausen Ottostr. 53": {
            "service_id": "ksr",
            "city": "Recklinghausen",
            "street": "Ottostr.",
            "house_number": "53",
        },
    }

    # service_id is always required. The place is given either by city name
    # (with optional street / house number) or directly by city_id + area_id;
    # alternatives() enforces exactly one of those two groups.
    PARAMS = [
        service_id("service_id"),
        alternatives(
            [city("city")],
            [city_id("city_id"), area_id("area_id")],
        ),
        street("street", optional=True),
        house_number("house_number", optional=True),
    ]

    HOWTO = {
        "en": (
            "Pick the 'service_id' for your region from the source's list of "
            "municipalities, then enter your town ('city') and where required "
            "the street ('street') and house number ('house_number'). "
            "Alternatively provide a known 'city_id' and 'area_id' directly."
        ),
        "de": (
            "Wählen Sie die 'service_id' Ihrer Region aus der Liste der Kommunen, "
            "geben Sie dann Ihren Ort ('city') an und, falls erforderlich, die "
            "Straße ('street') und Hausnummer ('house_number'). Alternativ können "
            "Sie eine bekannte 'city_id' und 'area_id' direkt angeben."
        ),
    }

    # Address/lookup source: an empty result means the input didn't resolve.
    RAISE_ON_EMPTY = True

    retrieve = JumomindRetriever(
        service_id="service_id",
        city="city",
        street="street",
        house_number="house_number",
        city_id="city_id",
        area_id="area_id",
    )
    parse = JumomindParser()
    transform = RowTransformer()

    def __init__(
        self,
        service_id: str,
        city: str | None = None,
        street: str | None = None,
        city_id=None,
        area_id=None,
        house_number=None,
    ):
        super().__init__(
            service_id=service_id,
            city=city,
            street=street,
            city_id=city_id,
            area_id=area_id,
            house_number=(str(house_number) if house_number is not None else None),
        )
