TITLE = "Landkreis Schwäbisch Hall (Broken)"
DESCRIPTION = "Broken Do not use anymore. Use app_abfallplus_de instead."
URL = "https://www.lrasha.de"

TEST_CASES = {"BROKEN": {"location": "BROKEN"}}


class Source:
    def __init__(self, location):
        raise Exception(
            "This source is no longer supported. Use app_abfallplus_de instead."
        )

    def fetch(self):
        raise Exception(
            "This source is no longer supported. Use app_abfallplus_de instead."
        )
