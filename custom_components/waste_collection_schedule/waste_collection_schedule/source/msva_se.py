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
        "postcode": "85461",
        "city": "Sundsvall",
    },
    "Västra Radiogatan 22, Sundsvall": {
        "street": "Västra Radiogatan",
        "house_number": "22",
        "postcode": "85461",
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


class Source:
    def __init__(
        self,
        street: str,
        house_number: str,
        postcode: str,
        city: str = "Sundsvall",
        additional_information: str = "",
    ):
        self._street = street
        self._house_number = str(house_number)
        self._postal_code = str(postcode)
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
                waste_label = WASTE_TYPE_MAP.get(item["wasteType"], item["wasteType"])
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
