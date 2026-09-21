import logging
from typing import ClassVar

from waste_collection_schedule import (  # type: ignore[attr-defined]
    Collection,
    Icons,
    date_parsers,
    field_terms,
    regions,
)
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    boolean,
    cascading_select,
    municipality,
)
from waste_collection_schedule.service.AffaldOnlineDk import (
    AffaldOnlineDkParser,
    AffaldOnlineDkRetriver,
    discover_choices,
)

_LOGGER = logging.getLogger("waste_collection_schedule.affaldonline_dk")

"""
Waste seperation in Denmark is mandetory to be atleast seperated into these 10 fractions:
Food Waste
Paper
Cardboard
Plastic
Food and drink cartons
Metal
Glass
Textiles
Hazardous waste
Residual waste

Only 6 out of the 10 types currently have a WasteType, the following are missing:
Cardboard, Plastic, Food and drink cartons, Metal

These 10 fractions are usually combined into bins for collection, with one or two compartments.
Some fractions are additionally allowed to be combined into the same compartment. As such some bins have 4 different fractions combined.

This makes the WasteType approach highly impractical, as some bins would end up with the same WasteType, even though it is a completely different bin and content.
For example take these two bins:
Metal, Glass, Paper & Cardboard
Plastic & Food and drink cartons

Both of these would under the current WasteType system end up as WasteType.RECYCLING, making for a confusing UX.

Instead the source currently uses the older direct Collection system, which offers more flexibility.
The API contains the exact fractions from each collection, and thus is able to dynamically name every collection based on the fraction content.
Additionally, if the user so desires, the param "split_bins" can be set. This splits each collection into separate collections, one for each fraction.
"""

"""
Maps fraction ID's to text and icon.
There are 90 fractions, however most are only used at recycling stations.
"""
FRACTION_MAP = {
    19: ("Elektronik", Icons.ELECTRONICS),
    27: ("Farligt affald", Icons.HAZARDOUS),
    41: ("Genbrug", Icons.RECYCLING),
    43: ("Madaffald", Icons.BIO_KITCHEN),
    46: ("Glas", Icons.GLASS),
    47: ("Papir", Icons.PAPER),
    50: ("Drikkedåser", Icons.METAL),
    51: ("Metal", Icons.METAL),
    53: ("Metal", Icons.METAL),
    54: ("Haveaffald", Icons.GARDEN),
    58: ("Pap", Icons.PAPER),
    59: ("Kartoner", Icons.PLASTIC_PACKAGING),
    72: ("Plast", Icons.PLASTIC_PACKAGING),
    78: ("Restaffald", Icons.GENERAL_WASTE),
    80: ("Restaffald", Icons.GENERAL_WASTE),
    81: ("Storskrald", Icons.BULKY),
    88: ("Tekstiler", Icons.TEXTILE),
    89: ("Madaffald", Icons.BIO_KITCHEN),
}


class Source(BaseSource):
    TITLE = "Affaldonline"
    DESCRIPTION = "Gather waste collection schedules from Affaldonline"
    URL = "https://affaldonline.dk"
    API_URL = "https://www.affaldonline.dk/api/address/collections"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@superrob"]

    REGIONS = regions.from_yaml("affaldonline_dk", title_suffix="affaldonline")

    TEST_CASES: ClassVar[dict] = {
        "aeroe": {
            "municipality": "aeroe",
            "street": "Nørregade|5970|Ærøskøbing",
            "values": "Nørregade|1||||5970|Ærøskøbing|1228262|448776|0",
        },
        "assens": {
            "municipality": "assens",
            "street": "Vandværksvej|5560|Aarup",
            "values": "Vandværksvej|2||||5560|Aarup|11266|456952|0",
        },
        "favrskov": {
            "municipality": "favrskov",
            "street": "Nørregade|8382|Hinnerup",
            "values": "Nørregade|1||||8382|Hinnerup|6443|108156|0",
        },
        "fanoe": {
            "municipality": "fanoe",
            "street": "Nørre Klit|6720|Fanø",
            "values": "Nørre Klit|5||||6720|Fanø|2582|1747246|0",
        },
        "fredericia": {
            "municipality": "fredericia",
            "street": "Nørre Allé|7000|Fredericia",
            "values": "Nørre Allé|5||||7000|Fredericia|11079971|1907927|0",
        },
        "ffv": {
            "municipality": "ffv",
            "street": "Marsk Billesvej|5672|Broby",
            "values": "Marsk Billesvej|18||||5672|Broby|36193544|576846|0",
        },
        "holbaek": {
            "municipality": "holbaek",
            "street": "Østerled|4300|Holbæk",
            "values": "Østerled|5||||4300|Holbæk|28441|1081575|2055",
        },
        "langeland": {
            "municipality": "langeland",
            "street": "Nørregade|5900|Rudkøbing",
            "values": "Nørregade|1||||5900|Rudkøbing|3535|383566|0",
        },
        "middelfart": {
            "municipality": "middelfart",
            "street": "Nørregade|5592|Ejby",
            "values": "Nørregade|2||||5592|Ejby|11288085|6496420|0",
        },
        "morsoe": {
            "municipality": "morsoe",
            "street": "Østervang|7900|Nykøbing M",
            "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        },
        "morsoe_split": {
            "municipality": "morsoe",
            "split_bins": True,
            "street": "Østervang|7900|Nykøbing M",
            "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        },
        "nyborg": {
            "municipality": "nyborg",
            "street": "Nørregade|5800|Nyborg",
            "values": "Nørregade|5||||5800|Nyborg|8896288|552542|0",
        },
        "silkeborg": {
            "municipality": "silkeborg",
            "street": "Nørregade|8620|Kjellerup",
            "values": "Nørregade|5||||8620|Kjellerup|45814316|1291964|0",
        },
        "rebild": {
            "municipality": "rebild",
            "street": "Nørregade|9500|Hobro",
            "values": "Nørregade|1||||9500|Hobro|11634418|19222228|0",
        },
        "vejle": {
            "municipality": "vejle",
            "values": "Nørregade|11||||7100|Vejle|16518799|16518799|0",
        },
        "viborg": {
            "municipality": "viborg",
            "street": "Hjultorvet|8800|Viborg",
            "values": "Hjultorvet|1||||8800|Viborg|8228245|8739|0",
        },
    }

    RAISE_ON_EMPTY = True
    PARAMS = (
        municipality("municipality"),
        boolean("split_bins", "Split bins into fractions"),
        cascading_select(
            ("street", field_terms.STREET),
            ("values", field_terms.HOUSE_NUMBER),
        ),
    )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Options for one cascade level given the levels chosen so far."""
        return discover_choices(field, selections)

    retrieve = AffaldOnlineDkRetriver()
    parse = AffaldOnlineDkParser()

    """
    Under the new WasteTypes paradime, this is "wrong".
    However the alternative would be both breaking and in many cases group multiple different containers into the same category.
    See the notes on the top of this file.
    """

    def classify(self, record):
        parse_date = date_parsers.for_format("%Y-%m-%d")
        date = parse_date(record["date"])
        if not date:
            return None
        if not record["fraction_name"]:
            return None
        fraction_names = []
        fraction_icon = Icons.GENERAL_WASTE
        for fraction_id in record["fraction_types"]:
            fraction_info = FRACTION_MAP.get(
                fraction_id, (f"{fraction_id} Mangler navn", Icons.GENERAL_WASTE)
            )
            fraction_names.append(fraction_info[0])
            fraction_icon = fraction_info[1]
        return Collection(
            date=date,
            t=fraction_names[0]
            if len(fraction_names) == 1
            else " og ".join([", ".join(fraction_names[:-1]), fraction_names[-1]]),
            icon=fraction_icon,
        )

    """
    This is the unused transformer aproach. Due to waste_type overlap.
    transform = JsonTransformer(
        date_key="date",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_key="type",
        description_key="type",
        type_value_map=TYPE_MAP,
        carry_raw_label=True,
    ) """
