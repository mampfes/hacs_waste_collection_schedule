from typing import ClassVar

from waste_collection_schedule import regions
from waste_collection_schedule import waste_types as wt
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
from waste_collection_schedule.service.Jumomind import (
    JumomindParser,
    JumomindRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Waste-type names come back as open-ended German labels that vary by provider,
# so this source declares NO per-source type map: the transformer resolves the
# standard German labels via the shared multilingual vocabulary
# (waste_types.resolve), and anything it doesn't recognise is preserved verbatim
# rather than collapsed to OTHER.


# Not @final: rh_entsorgung_de subclasses this for the RHE municipality.
class Source(BaseSource):
    TITLE = "Jumomind"
    DESCRIPTION = "Source for Jumomind.de waste collection."
    URL = "https://www.jumomind.de"
    COUNTRY = "de"
    # The transformer resolves open-ended German labels via the shared
    # vocabulary; the canonical types the providers actually emit (verified by
    # cassette replay) are declared here. Unrecognised labels stay preserved.
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    # One structure (the Jumomind mmapp API) covering many municipalities; the
    # full list is derived from the source's own provider registry at load time.
    REGIONS = regions.from_yaml(
        "jumomind_de", expand="cities", title_suffix="comment", service_id="service_id"
    )

    TEST_CASES: ClassVar[dict] = {
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
        "mymuell Senden, Birkenweg": {
            "service_id": "mymuell",
            "city": "Senden",
            "street": "Birkenweg (Senden)",
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
    PARAMS = (
        service_id("service_id"),
        alternatives(
            [city("city")],
            [city_id("city_id"), area_id("area_id")],
        ),
        street("street", optional=True),
        house_number("house_number", optional=True),
    )

    HOWTO: ClassVar[dict] = {
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
