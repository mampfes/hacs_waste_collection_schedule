import json
import logging
import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bayside Council (Victoria)"
DESCRIPTION = "Source for Bayside Council rubbish collection."
URL = "https://bayside.vic.gov.au"
TEST_CASES = {
    "76 Royal Avenue Sandringham": {"street_address": "76 Royal Avenue Sandringham"},
}

_LOGGER = logging.getLogger(__name__)

# IntraMaps API configuration
CONFIG_ID = "7a287c70-ea2d-4abd-943c-8bf55cf09fe5"
PROJECT_ID = "1c8f869f-fa4a-4c39-b7bb-94641ee61597"
FORM_ID = "a2f4b83c-a8ec-4ad8-83e4-f04f5d936077"

ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Food & Green Waste": "mdi:leaf",
    "Domestic Waste": "mdi:trash-can",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        # Step 1: Initialize IntraMaps session
        projects_url = "https://gis.bayside.vic.gov.au/IntraMaps910/ApplicationEngine/Projects/"
        params = {
            "configId": CONFIG_ID,
            "appType": "MapBuilder",
            "project": PROJECT_ID,
            "datasetCode": "",
        }

        response = session.post(projects_url, headers=headers, json={}, params=params)
        response.raise_for_status()

        if "X-IntraMaps-Session" not in response.headers:
            raise Exception("Failed to initialize IntraMaps session")

        sessionid = response.headers["X-IntraMaps-Session"]
        _LOGGER.debug("IntraMaps session ID: %s", sessionid)

        # Step 2: Load the Waste module
        modules_url = "https://gis.bayside.vic.gov.au/IntraMaps910/ApplicationEngine/Modules/"
        module_payload = json.dumps({
            "module": "Waste",
            "includeWktInSelection": True,
            "includeBasemaps": False,
        })
        params_module = {"IntraMapsSession": sessionid}

        response = session.post(
            modules_url, headers=headers, data=module_payload, params=params_module
        )
        response.raise_for_status()

        # Step 3: Search for the address
        search_url = "https://gis.bayside.vic.gov.au/IntraMaps910/ApplicationEngine/Search/"
        search_payload = json.dumps({"fields": [self._street_address]})
        search_params = {
            "infoPanelWidth": "350",
            "mode": "Refresh",
            "form": FORM_ID,
            "resubmit": "false",
            "IntraMapsSession": sessionid,
        }

        response = session.post(
            search_url, headers=headers, data=search_payload, params=search_params
        )
        response.raise_for_status()

        search_result = response.json()

        if not search_result.get("fullText") or len(search_result["fullText"]) == 0:
            raise Exception(
                f"Address search for '{self._street_address}' returned no results. "
                f"Try a simpler format like '76 Royal Avenue Sandringham' (without unit number or postcode)"
            )

        # Use the first match
        first_result = search_result["fullText"][0]
        map_key = first_result["mapKey"]
        db_key = first_result["dbKey"]
        selection_layer = first_result["selectionLayer"]

        _LOGGER.debug("Found address: %s", first_result.get("displayValue", "Unknown"))

        # Step 4: Get detailed waste collection information
        refine_url = "https://gis.bayside.vic.gov.au/IntraMaps910/ApplicationEngine/Search/Refine/Set"
        refine_payload = json.dumps({
            "selectionLayer": selection_layer,
            "mapKey": map_key,
            "dbKey": db_key,
            "infoPanelWidth": 350,
            "mode": "Refresh",
            "zoomType": "current",
        })
        refine_params = {"IntraMapsSession": sessionid}

        response = session.post(
            refine_url, headers=headers, data=refine_payload, params=refine_params
        )
        response.raise_for_status()

        refine_result = response.json()

        # Step 5: Parse waste collection data
        entries = []

        if "infoPanels" in refine_result:
            for panel_data in refine_result["infoPanels"].values():
                if not isinstance(panel_data, dict):
                    continue

                if panel_data.get("caption") == "Waste Collection Details":
                    if "feature" in panel_data and "fields" in panel_data["feature"]:
                        fields = panel_data["feature"]["fields"]

                        for field in fields:
                            field_name = field.get("name", "")
                            field_value_obj = field.get("value", {})

                            if isinstance(field_value_obj, dict):
                                field_value = field_value_obj.get("value", "")
                            else:
                                field_value = str(field_value_obj)

                            # Parse collection dates
                            if field_name in ["Recycling", "Domestic Waste", "Food & Green Waste"]:
                                entries.extend(
                                    self._parse_collection_field(field_name, field_value)
                                )

        return entries

    def _parse_collection_field(self, waste_type, value_text):
        """
        Parse collection field text like:
        - "Fortnightly on Wednesday, Next: 11 Feb 2026"
        - "Weekly on Wednesdays"
        """
        entries = []
        icon = ICON_MAP.get(waste_type, "mdi:trash-can-outline")

        # Extract the next collection date if present
        date_match = re.search(r"Next:\s*(\d{1,2}\s+\w+\s+\d{4})", value_text)
        if date_match:
            date_str = date_match.group(1)
            try:
                next_date = datetime.strptime(date_str, "%d %b %Y").date()

                # Determine if it's weekly or fortnightly
                is_fortnightly = "fortnightly" in value_text.lower()
                interval = 14 if is_fortnightly else 7

                # Generate next 4 collection dates
                for i in range(4):
                    collection_date = next_date + timedelta(days=i * interval)
                    entries.append(
                        Collection(date=collection_date, t=waste_type, icon=icon)
                    )

            except ValueError as e:
                _LOGGER.warning("Failed to parse date '%s': %s", date_str, e)

        # Handle "Weekly on [Day]" without explicit next date
        elif "weekly" in value_text.lower():
            # Extract the day of week
            day_match = re.search(r"on\s+(\w+day)", value_text, re.IGNORECASE)
            if day_match:
                day_name = day_match.group(1).lower().rstrip('s')  # Remove trailing 's' from "Wednesdays"

                # Map day names to weekday numbers (0=Monday, 6=Sunday)
                weekdays = {
                    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                    "friday": 4, "saturday": 5, "sunday": 6
                }

                if day_name in weekdays:
                    target_weekday = weekdays[day_name]
                    today = datetime.now().date()
                    current_weekday = today.weekday()

                    # Calculate days until next occurrence
                    days_ahead = target_weekday - current_weekday
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7

                    next_date = today + timedelta(days=days_ahead)

                    # Generate next 4 weekly collection dates
                    for i in range(4):
                        collection_date = next_date + timedelta(days=i * 7)
                        entries.append(
                            Collection(date=collection_date, t=waste_type, icon=icon)
                        )

        return entries
