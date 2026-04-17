from datetime import date

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Mittsverige Vatten & Avfall"
DESCRIPTION = "Source for Mittsverige Vatten & Avfall (MSVA) waste collection schedule, Sundsvall kommun."
URL = "https://www.msva.se"
TEST_CASES = {
    "Västra Radiogatan 18, Sundsvall": {
        "street": "Västra Radiogatan",
        "house_number": "18",
        "postal_code": "85461",
        "city": "Sundsvall",
    },
    "Västra Radiogatan 22, Sundsvall": {
        "street": "Västra Radiogatan",
        "house_number": "22",
        "postal_code": "85461",
        "city": "Sundsvall",
    },
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:leaf",
    "Pappersförpackningar": "mdi:package-variant",
    "Plastförpackningar": "mdi:recycle",
}

WASTE_TYPE_MAP = {
    "WASTE": "Restavfall",
    "FOOD": "Matavfall",
    "PAPER": "Pappersförpackningar",
    "PLASTIC": "Plastförpackningar",
}

API_URL = "https://api.sundsvall.se/Garbage/2281/schedules"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the full street address for a property in Sundsvall kommun. The API only supports Sundsvall (municipality code 2281) — Timrå and Nordanstig addresses are not covered. Use the same street, house number, postal code and city you would enter on msva.se.",
    "de": "Geben Sie die vollständige Adresse für ein Grundstück in der Gemeinde Sundsvall ein. Die API unterstützt nur Sundsvall (Gemeindecode 2281) — Adressen in Timrå und Nordanstig werden nicht abgedeckt.",
    "it": "Inserire l'indirizzo completo di una proprietà nel comune di Sundsvall. L'API supporta solo Sundsvall (codice comunale 2281); gli indirizzi di Timrå e Nordanstig non sono coperti.",
    "fr": "Saisissez l'adresse complète d'une propriété dans la commune de Sundsvall. L'API ne prend en charge que Sundsvall (code communal 2281) ; les adresses de Timrå et Nordanstig ne sont pas couvertes.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name without house number, e.g. 'Västra Radiogatan'.",
        "house_number": "House number, e.g. '18'.",
        "postal_code": "Five-digit Swedish postal code, e.g. '85461'.",
        "city": "Locality within Sundsvall kommun. Defaults to 'Sundsvall'.",
        "additional_information": "House letter or unit identifier, e.g. 'A'. Leave empty if not applicable.",
    },
    "de": {
        "street": "Straßenname ohne Hausnummer, z.B. 'Västra Radiogatan'.",
        "house_number": "Hausnummer, z.B. '18'.",
        "postal_code": "Fünfstellige schwedische Postleitzahl, z.B. '85461'.",
        "city": "Ortschaft innerhalb der Gemeinde Sundsvall. Standard: 'Sundsvall'.",
        "additional_information": "Hauskennung, z.B. 'A'. Leer lassen, falls nicht zutreffend.",
    },
    "it": {
        "street": "Nome della via senza numero civico, es. 'Västra Radiogatan'.",
        "house_number": "Numero civico, es. '18'.",
        "postal_code": "Codice postale svedese di cinque cifre, es. '85461'.",
        "city": "Località all'interno del comune di Sundsvall. Predefinito: 'Sundsvall'.",
        "additional_information": "Lettera o identificativo aggiuntivo, es. 'A'. Lasciare vuoto se non applicabile.",
    },
    "fr": {
        "street": "Nom de la rue sans numéro, ex. 'Västra Radiogatan'.",
        "house_number": "Numéro de maison, ex. '18'.",
        "postal_code": "Code postal suédois à cinq chiffres, ex. '85461'.",
        "city": "Localité dans la commune de Sundsvall. Par défaut : 'Sundsvall'.",
        "additional_information": "Lettre ou identifiant supplémentaire, ex. 'A'. Laisser vide si non applicable.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "house_number": "House number",
        "postal_code": "Postal code",
        "city": "City",
        "additional_information": "Additional information",
    },
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
        "postal_code": "Postleitzahl",
        "city": "Ort",
        "additional_information": "Zusatzinformation",
    },
    "it": {
        "street": "Via",
        "house_number": "Numero civico",
        "postal_code": "Codice postale",
        "city": "Città",
        "additional_information": "Informazioni aggiuntive",
    },
    "fr": {
        "street": "Rue",
        "house_number": "Numéro",
        "postal_code": "Code postal",
        "city": "Ville",
        "additional_information": "Informations complémentaires",
    },
}


class Source:
    def __init__(
        self,
        street: str,
        house_number: str,
        postal_code: str,
        city: str = "Sundsvall",
        additional_information: str = "",
    ):
        self._street = street
        self._house_number = str(house_number)
        self._postal_code = str(postal_code)
        self._city = city
        self._additional_information = additional_information

    def fetch(self) -> list[Collection]:
        params = {
            "street": self._street,
            "houseNumber": self._house_number,
            "postalCode": self._postal_code,
            "city": self._city,
        }
        if self._additional_information:
            params["additionalInformation"] = self._additional_information

        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()
        facilities = r.json()

        entries = []
        for facility in facilities:
            for item in facility.get("schedules", []):
                waste_label = WASTE_TYPE_MAP.get(
                    item["wasteType"], item["wasteType"]
                )
                entries.append(
                    Collection(
                        date=date.fromisoformat(item["nextPickupDate"]),
                        t=waste_label,
                        icon=ICON_MAP.get(waste_label),
                    )
                )

        if not entries:
            raise SourceArgumentException(
                "street",
                f"No schedule returned for {self._street} {self._house_number}, "
                f"{self._postal_code} {self._city}",
            )

        return entries
