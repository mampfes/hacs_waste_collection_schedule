from . import publidata_fr

TITLE = "GPSEO Waste Collection"
DESCRIPTION = "Source for GPSEO waste collection services."
URL = "https://dechets.gpseo.fr/"
COUNTRY = "fr"

TEST_CASES = {
    "Mantes la Ville": {"address": "11 rue Jean Moulin", "insee_code": "78362"},
    "Villennes sur Seine": {"address": "157 rue maurice utrillo", "insee_code": "78672"},
    "Poissy": {"address": "77 avenue Maurice Berteaux", "insee_code": "78498"},
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
        return super().__init__(address, insee_code, 1292)
