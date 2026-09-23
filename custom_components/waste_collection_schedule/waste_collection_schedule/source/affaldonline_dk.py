from typing import ClassVar

from waste_collection_schedule import (
    Collection,
    date_parsers,
    field_terms,
    regions,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    boolean,
    cascading_select,
    municipality,
)
from waste_collection_schedule.service.AffaldOnlineDk import (
    AffaldOnlineDkParser,
    AffaldOnlineDkRetriever,
    discover_choices,
)

"""
Waste separation in Denmark is mandatory to be at least separated into these 10 fractions:
Food Waste, Paper, Cardboard, Plastic, Food and drink cartons, Metal, Glass,
Textiles, Hazardous waste, Residual waste.

These 10 fractions are usually combined into bins for collection, with one or two
compartments. Some fractions are additionally allowed to be combined into the same
compartment, so some bins have up to 4 different fractions combined.

Every fraction resolves to a canonical WasteType (PAPER covers both paper and
cardboard - its English name is "Paper & Cardboard" - and RECYCLABLES covers the
mixed plastic/metal/carton packaging stream, matching the Danish "genbrug"
scheme). When a bin's fractions all resolve to the *same* canonical type, that
type is used directly. When a bin combines fractions that resolve to *different*
canonical types (e.g. "Restaffald og Madaffald" mixes GENERAL_WASTE and
FOOD_WASTE), collapsing it onto either one would misrepresent what is actually
being collected, so the provider's own composite label is kept verbatim via
waste_types.preserved() instead.

If the user so desires, the param "split_bins" can be set. This splits each
collection into separate collections, one per fraction - every one of those
then carries a single, canonical WasteType.
"""

# Fraction ID -> (Danish display label, canonical WasteType).
# There are 90 fractions in total, but most are only used at recycling stations.
FRACTION_MAP: dict[int, tuple[str, wt.WasteType]] = {
    19: ("Elektronik", wt.ELECTRONICS),
    27: ("Farligt affald", wt.HAZARDOUS),
    41: ("Genbrug", wt.RECYCLABLES),
    43: ("Madaffald", wt.FOOD_WASTE),
    46: ("Glas", wt.GLASS),
    47: ("Papir", wt.PAPER),
    50: ("Drikkedåser", wt.RECYCLABLES),
    51: ("Metal", wt.preserved("Metal")),
    53: ("Metal", wt.preserved("Metal")),
    54: ("Haveaffald", wt.GARDEN_WASTE),
    58: ("Pap", wt.PAPER),
    59: ("Kartoner", wt.preserved("Drinking cartons")),
    72: ("Plast", wt.preserved("Plastic")),
    78: ("Restaffald", wt.GENERAL_WASTE),
    80: ("Restaffald", wt.GENERAL_WASTE),
    81: ("Storskrald", wt.BULKY_WASTE),
    88: ("Tekstiler", wt.TEXTILES),
    89: ("Madaffald", wt.FOOD_WASTE),
}

# The distinct canonical types FRACTION_MAP resolves to. classify() may also
# emit a dynamic wt.preserved() label for a combined bin, but that is exempt
# from declaration (see tests/test_declared_waste_types.py).
_DECLARED_WASTE_TYPES = sorted(
    {waste_type.id: waste_type for _, waste_type in FRACTION_MAP.values()}.values(),
    key=lambda w: w.id,
)


class Source(BaseSource):
    TITLE = "Affaldonline"
    DESCRIPTION = "Gather waste collection schedules from Affaldonline"
    URL = "https://affaldonline.dk"
    COUNTRY = "dk"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@superrob"]
    WASTE_TYPES: ClassVar[list] = _DECLARED_WASTE_TYPES

    REGIONS = regions.from_yaml("affaldonline_dk", municipality="municipality")

    TEST_CASES: ClassVar[dict] = {
        "aeroe": {
            "municipality": "aeroe",
            "city": "Ærøskøbing",
            "street": "Nørregade|5970|Ærøskøbing",
            "values": "Nørregade|1||||5970|Ærøskøbing|4162588|448776|0",
        },
        "assens": {
            "municipality": "assens",
            "city": "Aarup",
            "street": "Vandværksvej|5560|Aarup",
            "values": "Vandværksvej|2||||5560|Aarup|11266|456952|0",
        },
        "favrskov": {
            "municipality": "favrskov",
            "city": "Hinnerup",
            "street": "Nørregade|8382|Hinnerup",
            "values": "Nørregade|1||||8382|Hinnerup|6443|108156|0",
        },
        "fanoe": {
            "municipality": "fanoe",
            "city": "Fanø",
            "street": "Nørre Klit|6720|Fanø",
            "values": "Nørre Klit|5||||6720|Fanø|2582|1747246|0",
        },
        "fredericia": {
            "municipality": "fredericia",
            "city": "Fredericia",
            "street": "Nørre Allé|7000|Fredericia",
            "values": "Nørre Allé|5||||7000|Fredericia|11079971|1907927|0",
        },
        "ffv": {
            "municipality": "ffv",
            "city": "Broby",
            "street": "Marsk Billesvej|5672|Broby",
            "values": "Marsk Billesvej|18||||5672|Broby|36193544|576846|0",
        },
        "holbaek": {
            "municipality": "holbaek",
            "city": "Holbæk",
            "street": "Østerled|4300|Holbæk",
            "values": "Østerled|5||||4300|Holbæk|28441|1081575|2055",
        },
        "langeland": {
            "municipality": "langeland",
            "city": "Rudkøbing",
            "street": "Nørregade|5900|Rudkøbing",
            "values": "Nørregade|1||||5900|Rudkøbing|3535|383566|0",
        },
        "middelfart": {
            "municipality": "middelfart",
            "city": "Ejby",
            "street": "Nørregade|5592|Ejby",
            "values": "Nørregade|2||||5592|Ejby|11288085|6496420|0",
        },
        "morsoe": {
            "municipality": "morsoe",
            "city": "Nykøbing M",
            "street": "Østervang|7900|Nykøbing M",
            "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        },
        "morsoe_split": {
            "municipality": "morsoe",
            "split_bins": True,
            "city": "Nykøbing M",
            "street": "Østervang|7900|Nykøbing M",
            "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        },
        "nyborg": {
            "municipality": "nyborg",
            "city": "Nyborg",
            "street": "Nørregade|5800|Nyborg",
            "values": "Nørregade|5||||5800|Nyborg|8896288|552542|0",
        },
        "silkeborg": {
            "municipality": "silkeborg",
            "city": "Kjellerup",
            "street": "Nørregade|8620|Kjellerup",
            "values": "Nørregade|5||||8620|Kjellerup|45814316|1291964|0",
        },
        "rebild": {
            "municipality": "rebild",
            "city": "Hobro",
            "street": "Nørregade|9500|Hobro",
            "values": "Nørregade|1||||9500|Hobro|11634418|19222228|0",
        },
        "vejle": {
            "municipality": "vejle",
            "city": "Vejle",
            "street": "Nørregade|7100|Vejle",
            "values": "Nørregade|11||||7100|Vejle|16518799|16518799|0",
        },
        "viborg": {
            "municipality": "viborg",
            "city": "Viborg",
            "street": "Hjultorvet|8800|Viborg",
            "values": "Hjultorvet|1||||8800|Viborg|8228245|8739|0",
        },
    }

    RAISE_ON_EMPTY = True
    PARAMS = (
        municipality("municipality"),
        boolean("split_bins", "Split bins into fractions"),
        cascading_select(
            ("city", field_terms.CITY),
            ("street", field_terms.STREET),
            ("values", field_terms.HOUSE_NUMBER),
        ),
    )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Options for one cascade level given the levels chosen so far."""
        return discover_choices(field, selections)

    retrieve = AffaldOnlineDkRetriever()
    parse = AffaldOnlineDkParser()

    def classify(self, record):
        parse_date = date_parsers.for_format("%Y-%m-%d")
        date = parse_date(record["date"])
        if not date:
            return None
        if not record["fraction_name"]:
            return None

        labels: list[str] = []
        # WasteType is unhashable (its aliases/names fields are dicts), so track
        # distinctness by id and keep one representative instance alongside it.
        resolved: list[wt.WasteType | None] = []
        for fraction_id in record["fraction_types"]:
            mapped = FRACTION_MAP.get(fraction_id)
            if mapped is None:
                # An uncatalogued fraction id: keep going so the label still
                # names it, but force the preserved() fallback below since we
                # don't know which canonical type it belongs to.
                labels.append(f"{fraction_id} Mangler navn")
                resolved.append(None)
                continue
            label, waste_type = mapped
            labels.append(label)
            resolved.append(waste_type)

        if not labels:
            # The provider named the bin but listed no fraction ids for it:
            # fall back to its own label rather than indexing an empty list.
            return Collection(
                date=date, waste_type=wt.preserved(record["fraction_name"])
            )

        distinct_ids = {w.id if w is not None else None for w in resolved}
        if len(distinct_ids) == 1 and None not in distinct_ids:
            # Every fraction in this bin resolves to the same canonical type:
            # using it directly loses nothing.
            return Collection(date=date, waste_type=resolved[0])

        # The bin combines fractions that resolve to more than one canonical
        # type (or includes one we don't recognise). Collapsing it onto any
        # single type would misrepresent what's actually being collected, so
        # keep the provider's own composite label verbatim instead.
        combined_label = (
            labels[0]
            if len(labels) == 1
            else " og ".join([", ".join(labels[:-1]), labels[-1]])
        )
        return Collection(date=date, waste_type=wt.preserved(combined_label))
