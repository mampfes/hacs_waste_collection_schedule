from waste_collection_schedule import Collection
from .awido_de import Source as AwidoSource


TITLE = "Landkreis Ebersberg"
DESCRIPTION = "Source for all municipalities in Landkreis Ebersberg."
URL = "https://www.lra-ebe.de/"
COUNTRY = "de"

# List of all 21 municipalities in Landkreis Ebersberg
MUNICIPALITIES = [
    "Anzing",
    "Aßling",
    "Baiern",
    "Bruck",
    "Ebersberg",
    "Egmating",
    "Emmering",
    "Forstinning",
    "Frauenneuharting",
    "Glonn",
    "Grafing",
    "Hohenlinden",
    "Kirchseeon",
    "Markt Schwaben",
    "Moosach",
    "Oberpframmern",
    "Pliening",
    "Poing",
    "Steinhöring",
    "Vaterstetten",
    "Zorneding",
]

def EXTRA_INFO():
    extra_info = [
        {
            "title": city if city.startswith(("Markt", "Stadt")) else f"Gemeinde {city}",
            "default_params": {"city": city},
        }
        for city in MUNICIPALITIES
    ]

    # Add aliases for Zorneding districts which don't require street/house number
    for alias in ["Pöring", "Wolfesing"]:
        extra_info.append({
            "title": f"{alias} (Zorneding)",
            "default_params": {"city": "Zorneding"},
        })

    return extra_info

TEST_CASES = {
    "Ebersberg": {"city": "Ebersberg"},
    "Poing": {"city": "Poing", "street": "Hauptstraße"},
    "Vaterstetten": {"city": "Vaterstetten", "street": "Fasanenstraße", "housenumber": 1},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your city and, if required, your street and house number. You can find the correct spelling and requirements on https://ebe.app.awido.de/home.",
    "de": "Wählen Sie Ihren Ort und, falls erforderlich, Ihre Straße und Hausnummer. Die korrekte Schreibweise und Anforderungen finden Sie unter https://ebe.app.awido.de/home.",
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "housenumber": "Hausnummer",
    }
}

ICON_MAP = {
    "restmüll": "mdi:trash-can",
    "biotonne": "mdi:leaf",
    "gelber sack": "mdi:recycle",
    "papier": "mdi:newspaper",  # Matches "Papiersamml. d. Vereine" and "Altpapier"
    "problemmüll": "mdi:biohazard",
    "gartenabfall": "mdi:flower",
    "christbaum": "mdi:pine-tree",
}

class Source(AwidoSource):
    def __init__(self, city: str, street: str | None = None, housenumber: str | int | None = None):
        super().__init__(customer="ebe", city=city, street=street, housenumber=housenumber)

    def fetch(self) -> list[Collection]:
        entries = super().fetch()
        for entry in entries:
            for name, icon in ICON_MAP.items():
                if name in entry.type.lower():
                    entry.set_icon(icon)
                    break
        return entries
