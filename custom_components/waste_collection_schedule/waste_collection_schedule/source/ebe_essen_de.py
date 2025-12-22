import requests
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "EBE Essen"
DESCRIPTION = "Source for EBE Essen (Entsorgungsbetriebe Essen) waste collection schedule"
URL = "https://www.ebe-essen.de/"
TEST_CASES = {
    "Altenessener Str. 15": {"street_id": "2175", "house_number": "15"},
}

API_URL = "https://widgets.abfall.io/graphql"

ICON_MAP = {
    "Blaue Tonne": "mdi:package-variant",
    "Braune Tonne": "mdi:leaf",
    "Gelbe Tonne": "mdi:recycle",
    "Graue Tonne": "mdi:trash-can",
    "Schadstoffmobil": "mdi:biohazard",
    "Weihnachtsbäume": "mdi:pine-tree",
}


class Source:
    def __init__(self, street_id: str, house_number: str):
        self._street_id = street_id
        self._house_number = house_number

    def fetch(self):
        # Step 1: Get house number ID from street
        house_number_id = self._get_house_number_id()

        # Step 2: Get waste types for house number
        waste_type_ids = self._get_waste_types(house_number_id)

        # Step 3: Get appointments for house number and waste types
        return self._get_appointments(house_number_id, waste_type_ids)

    def _get_house_number_id(self):
        """Get house number ID from street ID"""
        query = "query GetHouseNumbers($streetId: ID!, $idDistrict: ID, $query: String) { street(id: $streetId) { houseNumbers(query: $query, idDistrict: $idDistrict) { id name } } }"
        
        variables = {
            "streetId": self._street_id,
            "query": None,
            "idDistrict": None
        }

        r = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://www.ebe-essen.de",
                "Referer": "https://www.ebe-essen.de/",
                "x-abfallplus-api-key": "MTEwYzI4ODMtNmMzOC00MTlkLTkzZTUtZDJhYjUxNTUwYzk1OjU4NDM="
            }
        )
        r.raise_for_status()
        data = r.json()

        house_numbers = data.get("data", {}).get("street", {}).get("houseNumbers", [])
        
        for hn in house_numbers:
            if hn["name"] == self._house_number:
                return hn["id"]
        
        raise Exception(f"House number {self._house_number} not found for street {self._street_id}")

    def _get_waste_types(self, house_number_id: str):
        """Get waste type IDs for house number"""
        query = "query HouseNumber($houseNumberId: ID!) { houseNumber(id: $houseNumberId) { wasteTypes { id name internals { pdfLegend } } } }"
        
        variables = {"houseNumberId": house_number_id}

        r = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://www.ebe-essen.de",
                "Referer": "https://www.ebe-essen.de/",
                "x-abfallplus-api-key": "MTEwYzI4ODMtNmMzOC00MTlkLTkzZTUtZDJhYjUxNTUwYzk1OjU4NDM="
            }
        )
        r.raise_for_status()
        data = r.json()

        waste_types = data.get("data", {}).get("houseNumber", {}).get("wasteTypes", [])
        
        # Filter out Schadstoffmobil types (we only want the main waste types)
        filtered_types = []
        for wt in waste_types:
            name = wt["name"]
            # Include main waste types and Christmas trees, exclude district-specific Schadstoffmobil
            if not name.startswith("Schadstoffmobil ") or name == "Schadstoffmobil":
                filtered_types.append(wt["id"])
        
        return filtered_types

    def _get_appointments(self, house_number_id: str, waste_type_ids: list):
        """Get waste collection appointments"""
        query = "query Query($idHouseNumber: ID!, $wasteTypes: [ID], $dateMin: Date, $dateMax: Date, $showInactive: Boolean) { appointments(idHouseNumber: $idHouseNumber, wasteTypes: $wasteTypes, dateMin: $dateMin, dateMax: $dateMax, showInactive: $showInactive) { id date time location note wasteType { id name color internals { pdfLegend iconHigh } } } }"
        
        # Get current year and next year
        current_year = datetime.now().year
        
        variables = {
            "idHouseNumber": house_number_id,
            "wasteTypes": waste_type_ids,
            "dateMin": f"{current_year}-01-01",
            "dateMax": f"{current_year + 1}-12-31",
            "showInactive": False
        }

        r = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://www.ebe-essen.de",
                "Referer": "https://www.ebe-essen.de/",
                "x-abfallplus-api-key": "MTEwYzI4ODMtNmMzOC00MTlkLTkzZTUtZDJhYjUxNTUwYzk1OjU4NDM="
            }
        )
        r.raise_for_status()
        data = r.json()

        appointments = data.get("data", {}).get("appointments", [])

        entries = []
        for appointment in appointments:
            date_str = appointment.get("date")
            if not date_str:
                continue

            try:
                date = datetime.fromisoformat(date_str).date()
            except ValueError:
                continue

            waste_type = appointment.get("wasteType", {})
            waste_name = waste_type.get("name", "Unknown")

            # Find icon
            icon = "mdi:trash-can"
            for key, ico in ICON_MAP.items():
                if key in waste_name:
                    icon = ico
                    break

            entries.append(
                Collection(
                    date=date,
                    t=waste_name,
                    icon=icon,
                )
            )

        return entries
