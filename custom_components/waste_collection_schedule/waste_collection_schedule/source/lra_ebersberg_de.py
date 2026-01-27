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
    "en": "Select your city and, if required, your street and house number. You can verify requirements in the official 'Abfall-App Ebersberg'.",
    "de": "Wählen Sie Ihren Ort und, falls erforderlich, Ihre Straße und Hausnummer. Die Anforderungen können Sie in der offiziellen 'Abfall-App Ebersberg' prüfen.",
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "housenumber": "Hausnummer",
    }
}

class Source(AwidoSource):
    def __init__(self, city: str, street: str | None = None, housenumber: str | int | None = None):
        super().__init__(customer="ebe", city=city, street=street, housenumber=housenumber)
