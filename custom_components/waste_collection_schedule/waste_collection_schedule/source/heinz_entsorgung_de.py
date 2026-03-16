import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Heinz-Entsorgung (Landkreis Freising)"
DESCRIPTION = "Source for Heinz-Entsorgung (Landkreis Freising) waste collection."
URL = "https://abfallkalender.heinz-entsorgung.de/"
TEST_CASES = {
    "Test_Freising": {
        "param": "yesJWYk53alJXaiMiOMJWYk53alJXagMnRlJXapNmbicCLvJnciQiOBJGblxncoNXYzVWZi4CLzJHdhJ3clNjIioWTv93c0Nici4CLqJWYyhjIiojMyASN9J"
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": """To get the required parameter:
1. Open https://abfallkalender.heinz-entsorgung.de/ in your browser
2. Open the browser's Developer Tools (F12)
3. Go to the 'Network' tab
4. Select your location (Ort) and street (Straße)
5. Look for a request to 'api-enttermine.heinz-entsorgung.net/termine'
6. Copy the 'param' value from the URL query string
7. Use this value as the 'param' argument

Note: The parameter is encrypted and specific to your location and street selection.
""",
    "de": """So erhalten Sie den erforderlichen Parameter:
1. Öffnen Sie https://abfallkalender.heinz-entsorgung.de/ in Ihrem Browser
2. Öffnen Sie die Entwicklertools des Browsers (F12)
3. Gehen Sie zum Tab 'Netzwerk'
4. Wählen Sie Ihren Ort und Ihre Straße aus
5. Suchen Sie nach einer Anfrage an 'api-enttermine.heinz-entsorgung.net/termine'
6. Kopieren Sie den 'param'-Wert aus der URL-Abfragezeichenfolge
7. Verwenden Sie diesen Wert als 'param'-Argument

Hinweis: Der Parameter ist verschlüsselt und spezifisch für Ihre Orts- und Straßenauswahl.
""",
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Gelber Sack": "mdi:recycle",
    "Bioabfall": "mdi:leaf",
    "BIO": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Problemmüll": "mdi:flask",
    "Sperrmüll": "mdi:sofa",
}

API_URL = "https://api-enttermine.heinz-entsorgung.net/termine"


class Source:
    def __init__(self, param: str):
        self._param = param

    def fetch(self) -> list[Collection]:
        # Make API request
        r = requests.get(API_URL, params={"param": self._param})
        r.raise_for_status()

        data = json.loads(r.text)

        entries = []
        for item in data:
            date_str = item.get("termin")
            if not date_str:
                continue

            # Parse date (format: YYYY-MM-DD)
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Get waste type
            waste_type = item.get("fraktion", "Unknown")
            
            # Get additional info if available
            zusatz = item.get("zusatz", "")
            if zusatz:
                waste_type = f"{waste_type} ({zusatz})"

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.split(" (")[0], "mdi:trash-can"),
                )
            )

        return entries
