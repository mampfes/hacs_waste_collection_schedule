"""Standard waste collection type definitions + multilingual resolution.

Each WasteType is a canonical category with a stable id, icon, colour, localised
display ``names`` and a set of ``aliases`` (known labels/synonyms per language).

Sources do NOT need to hand-map every local label. ``resolve(label)`` matches a
raw label (in any supported language) against names + aliases and returns the
canonical WasteType. A label that genuinely isn't recognised is preserved
verbatim via ``preserved(label)`` (shown as-is, never silently turned into
"Other"), and a warning is logged so the alias can be curated in.
"""

import logging
from dataclasses import dataclass, field

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WasteType:
    """A standard waste collection category."""

    id: str
    icon: str
    color: str
    names: dict[str, str]
    # Known labels/synonyms per language, used by resolve(). Unambiguous only:
    # avoid region-ambiguous labels (e.g. "green bin") that map differently.
    aliases: dict[str, list[str]] = field(default_factory=dict)


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
    aliases={
        "en": [
            "residual waste",
            "rubbish",
            "refuse",
            "trash",
            "garbage",
            "domestic waste",
        ],
        "de": [
            "restabfall",
            "graue tonne",
            "schwarze tonne",
            "hausmüll",
            "restmülltonne",
        ],
        "fr": ["déchets résiduels", "ordures"],
        "it": ["indifferenziato", "secco", "secco residuo"],
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
    aliases={
        "en": [
            "recyclables",
            "recycle",
            "mixed recycling",
            "commingled",
            "containers",
            "packaging",
        ],
        "de": [
            "wertstofftonne",
            "gelber sack",
            "gelbe tonne",
            "leichtverpackungen",
            "lvp",
            "verpackungen",
            "wertstoffsack",
        ],
        "fr": ["recyclables", "emballages", "tri sélectif", "bac jaune"],
        "it": ["imballaggi", "plastica e lattine", "multimateriale"],
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
    aliases={
        "en": ["organic", "biowaste", "fogo", "food and garden"],
        "de": ["bioabfall", "biotonne", "bio"],
        "fr": ["déchets organiques"],
        "it": ["umido", "frazione organica"],
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
    aliases={
        "en": ["paper", "cardboard", "paper and card", "blue bin"],
        "de": [
            "papier",
            "papiertonne",
            "blaue tonne",
            "pappe",
            "papier und pappe",
            "ppk",
        ],
        "fr": ["carton", "papiers", "papier et carton"],
        "it": ["carta", "cartone"],
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
    aliases={
        "en": ["glass bottles"],
        "de": ["altglas", "glascontainer"],
        "it": ["vetro e lattine"],
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
    aliases={
        "en": ["food", "food scraps", "food caddy"],
        "de": ["speisereste", "küchenabfälle"],
        "it": ["scarti alimentari"],
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
    aliases={
        "en": [
            "green waste",
            "garden",
            "yard waste",
            "yard trimmings",
            "christmas trees",
            "leaves",
        ],
        "de": [
            "gartenabfall",
            "grünabfall",
            "gartenabfälle",
            "baum- und strauchschnitt",
            "strauchschnitt",
            "laub",
            "weihnachtsbäume",
            "tannenbäume",
            "christbäume",
        ],
        "fr": ["déchets de jardin", "sapins de noël"],
        "it": ["sfalci e potature", "verde"],
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
    aliases={
        "en": ["bulky", "bulk waste", "hard waste", "large items"],
        "de": ["sperrgut", "grobmüll"],
        "fr": ["objets encombrants"],
        "it": ["rifiuti ingombranti"],
    },
)

HAZARDOUS = WasteType(
    id="hazardous",
    icon="mdi:biohazard",
    color="#E53935",
    names={
        "en": "Hazardous Waste",
        "de": "Problemstoff",
        "fr": "Déchets dangereux",
        "it": "Rifiuti pericolosi",
    },
    aliases={
        "en": ["hazardous", "household hazardous waste", "hhw", "chemicals"],
        "de": [
            "problemstoffe",
            "schadstoff",
            "schadstoffe",
            "sonderabfall",
            "sondermüll",
            "schadstoffmobil",
            "giftmüll",
        ],
        "fr": ["déchets toxiques"],
    },
)

ELECTRONICS = WasteType(
    id="electronics",
    icon="mdi:television-classic",
    color="#5E35B1",
    names={
        "en": "Electronic Waste",
        "de": "Elektroschrott",
        "fr": "Déchets électroniques",
        "it": "Rifiuti elettronici",
    },
    aliases={
        "en": ["electronics", "e-waste", "weee", "white goods", "appliances"],
        "de": [
            "elektro",
            "elektrogeräte",
            "elektroaltgeräte",
            "e-schrott",
            "weiße ware",
            "weiße waren",
            "kühlgeräte",
            "elektronikschrott",
        ],
        "fr": ["deee", "électroménager"],
        "it": ["raee"],
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
    HAZARDOUS,
    ELECTRONICS,
    OTHER,
]


def _norm(label: str) -> str:
    """Normalise a label for matching: trim, lower-case, collapse whitespace."""
    return " ".join(str(label).strip().lower().split())


def _build_index() -> dict[str, WasteType]:
    """Index every canonical type's display names + aliases by normalised label.

    OTHER is excluded (it's only used when a source maps to it explicitly).
    First definition wins on collisions, with a warning, so the vocabulary stays
    unambiguous.
    """
    index: dict[str, WasteType] = {}
    for waste_type in ALL_TYPES:
        if waste_type is OTHER:
            continue
        labels = list(waste_type.names.values())
        for synonyms in waste_type.aliases.values():
            labels.extend(synonyms)
        for label in labels:
            key = _norm(label)
            existing = index.get(key)
            if existing is not None and existing is not waste_type:
                _LOGGER.warning(
                    "Ambiguous waste-type alias %r (%s vs %s); keeping %s",
                    label,
                    existing.id,
                    waste_type.id,
                    existing.id,
                )
                continue
            index[key] = waste_type
    return index


_INDEX = _build_index()


def resolve(label: str) -> WasteType | None:
    """Return the canonical WasteType for a raw label (any language), or None.

    Matches the normalised label against every type's display names and aliases.
    """
    return _INDEX.get(_norm(label))


def preserved(label: str) -> WasteType:
    """Return an ad-hoc WasteType that carries an unrecognised label verbatim.

    Used as the no-loss fallback when ``resolve`` finds nothing: the original
    text is shown in every locale (we can't translate it), the id is prefixed
    ``preserved:`` so it's distinguishable, and it borrows OTHER's icon/colour.
    """
    text = str(label).strip()
    return WasteType(
        id=f"preserved:{_norm(label)}",
        icon=OTHER.icon,
        color=OTHER.color,
        names={lang: text for lang in ("en", "de", "fr", "it")},
    )
