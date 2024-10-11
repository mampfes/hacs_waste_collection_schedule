from . import publidata_fr

TITLE = "Tours Métropole Waste Collection"
DESCRIPTION = "Source for Tours Métropole waste collection services."
URL = "https://www.tours-metropole.fr/mes-poubelles-connaitre-les-jours-de-collecte-et-sinformer-sur-le-tri"
COUNTRY = "fr"

TEST_CASES = {
    "Ballan-Miré": {"address": "3 Rue de Miré", "insee_code": "37018"},
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
        return super().__init__(address, insee_code, 65)
