import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Bad Aussee"
DESCRIPTION = "Source for Bad Aussee, Austria"
URL = "https://www.badaussee.at"
TEST_CASES = {
    "Zone 1": {
        "restmuell_zone": "1",
        "biomuell_zone": "1",
        "altpapier_zone": "1",
    },
    "Zone 4": {
        "restmuell_zone": "4",
        "biomuell_zone": "4",
        "altpapier_zone": "4",
    },
}

ICS_BASE_URL = "https://www.badaussee.at/system/web/CalendarService.ashx"
ICS_PARAMS = {
    "aqn": (
        "UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4w"
        "LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw="
    ),
    "sprache": "1",
    "gnr": "3138",
}

# Mapping of zone codes to their ICS 'do' parameter values
ICS_ZONE_MAPPING = {
    "gelber_sack": "MjI1MjYyNTgx",  # gs
    "restmuell": {
        "1": "MjI1MjYyNTQw",
        "2": "MjI1MjYyNTY4",
        "3": "MjI1MjYyNTY5",
        "4": "MjI1MjYyNTcw",
        "5": "MjI1MjYyNTcx",
        "6": "MjI1MjYyNTcy",
    },
    "biomuell": {
        "1": "MjI1MjYyNTcz",
        "2": "MjI1MjYyNTc0",
        "3": "MjI1MjYyNTc1",
        "4": "MjI1MjYyNTc2",
    },
    "altpapier": {
        "1": "MjI1MjYyNTc3",
        "2": "MjI1MjYyNTc4",
        "3": "MjI1MjYyNTc5",
        "4": "MjI1MjYyNTgw",
    },
}

ICON_MAP = {
    "Gelber Sack": "mdi:sack",
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Altpapier": "mdi:package-variant",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "restmuell_zone": "Zone number for residual waste (Restmüll)",
        "biomuell_zone": "Zone number for organic waste (Biomüll)",
        "altpapier_zone": "Zone number for paper waste (Altpapier)",
    },
    "de": {
        "restmuell_zone": "Zonennummer für Restmüll",
        "biomuell_zone": "Zonennummer für Biomüll",
        "altpapier_zone": "Zonennummer für Altpapier",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "restmuell_zone": "Residual Waste Zone",
        "biomuell_zone": "Organic Waste Zone",
        "altpapier_zone": "Paper Waste Zone",
    },
    "de": {
        "restmuell_zone": "Restmüll Zone",
        "biomuell_zone": "Biomüll Zone",
        "altpapier_zone": "Altpapier Zone",
    },
}


class Source:
    def __init__(
        self,
        restmuell_zone: str | int = "",
        biomuell_zone: str | int = "",
        altpapier_zone: str | int = "",
    ):
        self._restmuell_zone = str(restmuell_zone) if restmuell_zone else ""
        self._biomuell_zone = str(biomuell_zone) if biomuell_zone else ""
        self._altpapier_zone = str(altpapier_zone) if altpapier_zone else ""
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        entries = []

        # Always include Gelber Sack
        ics_urls = [self._build_ics_url(ICS_ZONE_MAPPING["gelber_sack"])]

        # Add zone-specific URLs based on configured zones
        if self._restmuell_zone and self._restmuell_zone in ICS_ZONE_MAPPING["restmuell"]:
            ics_urls.append(self._build_ics_url(ICS_ZONE_MAPPING["restmuell"][self._restmuell_zone]))

        if self._biomuell_zone and self._biomuell_zone in ICS_ZONE_MAPPING["biomuell"]:
            ics_urls.append(self._build_ics_url(ICS_ZONE_MAPPING["biomuell"][self._biomuell_zone]))

        if self._altpapier_zone and self._altpapier_zone in ICS_ZONE_MAPPING["altpapier"]:
            ics_urls.append(self._build_ics_url(ICS_ZONE_MAPPING["altpapier"][self._altpapier_zone]))

        # Fetch and parse each ICS feed
        for ics_url in ics_urls:
            r = requests.get(ics_url, timeout=60)
            r.raise_for_status()

            # Parse ICS data
            dates = self._ics.convert(r.text)

            # Convert to Collection objects
            for d in dates:
                waste_type = d[1].strip()

                # Determine icon based on waste type
                icon = "mdi:trash-can-outline"
                for key, value in ICON_MAP.items():
                    if key.lower() in waste_type.lower():
                        icon = value
                        break

                entries.append(
                    Collection(
                        date=d[0],
                        t=waste_type,
                        icon=icon,
                    )
                )

        return entries

    def _build_ics_url(self, do_param: str) -> str:
        """Build ICS URL with the given 'do' parameter."""
        params = {**ICS_PARAMS, "do": do_param}
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{ICS_BASE_URL}?{param_str}"
