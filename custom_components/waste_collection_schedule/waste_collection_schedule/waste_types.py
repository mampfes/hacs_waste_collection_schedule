"""Standard waste collection type definitions.

Each WasteType represents a fundamental category of waste collection.
Sources classify local waste names into these standard types via their
classify() method. The framework handles presentation (icon, colour,
label, translation) and user overrides.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WasteType:
    """A standard waste collection category."""

    id: str
    icon: str
    color: str
    names: dict[str, str]


GENERAL_WASTE = WasteType(
    id="general_waste",
    icon="mdi:trash-can",
    color="#6B6B6B",
    names={
        "en": "General Waste",
        "de": "Restmüll",
        "fr": "Ordures ménagères",
        "it": "Rifiuto indifferenziato",
    },
)

RECYCLABLES = WasteType(
    id="recyclables",
    icon="mdi:recycle",
    color="#2196F3",
    names={
        "en": "Recycling",
        "de": "Wertstoffe",
        "fr": "Recyclage",
        "it": "Differenziata",
    },
)

ORGANIC = WasteType(
    id="organic",
    icon="mdi:leaf",
    color="#4CAF50",
    names={
        "en": "Organic Waste",
        "de": "Biomüll",
        "fr": "Biodéchets",
        "it": "Organico",
    },
)

PAPER = WasteType(
    id="paper",
    icon="mdi:package-variant",
    color="#795548",
    names={
        "en": "Paper & Cardboard",
        "de": "Altpapier",
        "fr": "Papier",
        "it": "Carta e cartone",
    },
)

GLASS = WasteType(
    id="glass",
    icon="mdi:bottle-wine",
    color="#009688",
    names={
        "en": "Glass",
        "de": "Glas",
        "fr": "Verre",
        "it": "Vetro",
    },
)

FOOD_WASTE = WasteType(
    id="food_waste",
    icon="mdi:food-apple",
    color="#FF9800",
    names={
        "en": "Food Waste",
        "de": "Lebensmittelabfall",
        "fr": "Déchets alimentaires",
        "it": "Rifiuto alimentare",
    },
)

GARDEN_WASTE = WasteType(
    id="garden_waste",
    icon="mdi:tree",
    color="#2E7D32",
    names={
        "en": "Garden Waste",
        "de": "Grünschnitt",
        "fr": "Déchets verts",
        "it": "Rifiuto verde",
    },
)

BULKY_WASTE = WasteType(
    id="bulky_waste",
    icon="mdi:sofa",
    color="#607D8B",
    names={
        "en": "Bulky Waste",
        "de": "Sperrmüll",
        "fr": "Encombrants",
        "it": "Ingombranti",
    },
)

OTHER = WasteType(
    id="other",
    icon="mdi:calendar",
    color="#9E9E9E",
    names={
        "en": "Other",
        "de": "Sonstiges",
        "fr": "Autres",
        "it": "Altro",
    },
)

ALL_TYPES = [
    GENERAL_WASTE,
    RECYCLABLES,
    ORGANIC,
    PAPER,
    GLASS,
    FOOD_WASTE,
    GARDEN_WASTE,
    BULKY_WASTE,
    OTHER,
]
