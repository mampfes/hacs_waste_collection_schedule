from waste_collection_schedule.source.abfall_io import Source as AbfallIOSource

TITLE = "Stadt Kerpen"
DESCRIPTION = "Source for waste collection services in Kerpen."
URL = "https://www.stadt-kerpen.de"
COUNTRY = "de"

TEST_CASES = {
    "Amselweg": {
        "f_id_strasse": "3703amselweg",
        "f_id_strasse_hnr": "19409",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "f_id_strasse": "Street",
        "f_id_strasse_hnr": "House Number",
        "f_abfallarten": "Waste Types",
    },
    "de": {
        "f_id_strasse": "Straße",
        "f_id_strasse_hnr": "Hausnummer",
        "f_abfallarten": "Abfallarten",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "f_id_strasse": "The internal ID of your street (use the wizard to get this)",
        "f_id_strasse_hnr": "The internal ID of your house number (use the wizard to get this)",
        "f_abfallarten": "List of waste types (internal IDs). Leave empty to get all.",
    },
    "de": {
        "f_id_strasse": "Die interne ID der Straße (nutzen Sie den Wizard, um diese zu ermitteln)",
        "f_id_strasse_hnr": "Die interne ID der Hausnummer (nutzen Sie den Wizard, um diese zu ermitteln)",
        "f_abfallarten": "Liste der Abfallarten (interne IDs). Leer lassen, um alle abzurufen.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can get the internal IDs for the street and house number by using the abfall_io wizard script (`custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io.py`) or by inspecting the network traffic on the provider's MüllALARM website. The commune ID is preconfigured for Kerpen.",
    "de": "Sie können die internen IDs für die Straße und Hausnummer über das abfall_io Wizard Skript (`custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io.py`) oder durch das Analysieren des Netzwerkverkehrs auf der MüllALARM Webseite des Anbieters ermitteln. Die ID der Kommune ist für Kerpen vorkonfiguriert.",
}


class Source(AbfallIOSource):
    def __init__(self, f_id_strasse, f_id_strasse_hnr=None, f_abfallarten=None):
        super().__init__(
            key="e5543a3e190cb8d91c645660ad60965f",
            f_id_kommune=3703,
            f_id_strasse=f_id_strasse,
            f_id_strasse_hnr=f_id_strasse_hnr,
            f_abfallarten=f_abfallarten,
        )
