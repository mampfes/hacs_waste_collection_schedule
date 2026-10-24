from typing import ClassVar, final

from waste_collection_schedule import regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    api_key,
    dropdown,
    integer,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.field_terms import HOUSE_NUMBER
from waste_collection_schedule.service.Geovest import GeovestParser, GeovestRetriever
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Verde leggero": wt.GARDEN_WASTE,
    "Verde": wt.GARDEN_WASTE,
    "Organico": wt.ORGANIC,
    "Umido": wt.ORGANIC,
    "Indifferenziato": wt.GENERAL_WASTE,
    "Rifiuti indifferenziati": wt.GENERAL_WASTE,
    "Carta": wt.PAPER,
    "Cartone": wt.PAPER,
    "Imballaggi in plastica": wt.PLASTIC,
    "Plastica": wt.PLASTIC,
    "Metalli": wt.METAL,
    "Vetro": wt.GLASS,
}

# The address search returns the street on its own ("VIA GRAMSCI"), so the
# published test names "via antonio gramsci" and "via oreste vancini" no longer
# match. The two cases below are streets the API currently returns.
_TOWNS = (
    ("Anzola dell'Emilia", "7"),
    ("Argelato", "12"),
    ("Calderara di Reno", "8"),
    ("Castel Maggiore", "10"),
    ("Crevalcore", "2"),
    ("Finale Emilia", "1"),
    ("Nonantola", "6"),
    ("Ravarino", "9"),
    ("Sala Bolognese", "4"),
    ("San Giovanni in Persiceto", "5"),
    ("Sant'Agata Bolognese", "13"),
)


@final
class Source(BaseSource):
    TITLE = "Geovest"
    DESCRIPTION = "Source for Geovest, Italy."
    URL = "https://geovest.bluemilk.dev"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.PLASTIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Via Gramsci": {
            "town_id": "7",
            "numbers": "228",
            "address_name": "via gramsci",
            "device_id": "1111111111111111",
        },
        "Piazza Giovanni XXIII": {
            "town_id": "7",
            "numbers": "1",
            "address_name": "piazza giovanni xxiii",
            "device_id": "2222222222222222",
        },
    }

    PARAMS = (
        street(field="address_name"),
        municipality(field="town_id"),
        text_field("numbers", term=HOUSE_NUMBER, default="1"),
        dropdown(
            "calendar_type_id",
            ["1", "2"],
            label="Calendar Type",
            default="1",
        ),
        integer("days", label="Days to fetch", default=30),
        text_field("device_id", label="Device ID", optional=True),
        api_key("authorization", default="Bearer MTga45Xm8YAK"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your town id from the Geovest list, then search your street "
            "name. The house number defaults to 1 and is only used when several "
            "streets match. A device id is generated when you leave it empty. "
            "Replace the authorization token only if the built-in one stops working. "
            "Calendar type 1 is a private address and 2 is a business."
        ),
    }

    REGIONS = tuple(regions.region(title, town_id=town_id) for title, town_id in _TOWNS)

    retrieve = GeovestRetriever()
    parse = GeovestParser()
    transform = RowTransformer(type_value_map=_TYPE_MAP)
