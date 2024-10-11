from . import publidata_fr

TITLE = "Orléans Métropole Waste Collection"
DESCRIPTION = "Source for Orléans Métropole waste collection services."
URL = "https://triermondechet.orleans-metropole.fr/"
COUNTRY = "fr"

TEST_CASES = {
    "Boigny sur Bionne": {"address": "13 rue de la Commanderie", "insee_code": "45034"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "The INSEE code, different from postal code, can easily be found on Google",
    "de": "Der INSEE-Code, der sich vom Postleitzahl unterscheidet, kann leicht auf Google gefunden werden",
    "it": "Il codice INSEE, diverso dal codice postale, può essere facilmente trovato su Google",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your full address",
        "insee_code": "The 5-digit INSEE code of your commune",
    },
    "de": {
        "address": "Ihre vollständige Adresse",
        "insee_code": "Der 5-stellige INSEE-Code Ihrer Gemeinde",
    },
    "it": {
        "address": "Il tuo indirizzo completo",
        "insee_code": "Il codice INSEE a 5 cifre del tuo comune",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
        "insee_code": "INSEE Code",
    },
    "de": {
        "address": "Adresse",
        "insee_code": "INSEE-Code",
    },
    "it": {
        "address": "Indirizzo",
        "insee_code": "Codice INSEE",
    },
}

class Source(publidata_fr.Source):
    def __init__(self, address, insee_code):
        return super().__init__(address, insee_code, 100)
