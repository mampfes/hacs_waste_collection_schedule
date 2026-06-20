from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Bad Aussee"
DESCRIPTION = "Source for Bad Aussee, Austria"
URL = "https://www.badaussee.at"
COUNTRY = "at"
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
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
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


class Source(RiSKommunalSource):
    BASE_URL = "https://www.badaussee.at"
    ICON_MAP = ICON_MAP
    GNR = "3138"

    def __init__(
        self,
        restmuell_zone: str | int = "",
        biomuell_zone: str | int = "",
        altpapier_zone: str | int = "",
    ):
        super().__init__()
        self._restmuell_zone = str(restmuell_zone) if restmuell_zone else ""
        self._biomuell_zone = str(biomuell_zone) if biomuell_zone else ""
        self._altpapier_zone = str(altpapier_zone) if altpapier_zone else ""

    def fetch(self):
        # Always include Gelber Sack, then add the configured zone calendars.
        do_ids = [ICS_ZONE_MAPPING["gelber_sack"]]

        for key, zone in (
            ("restmuell", self._restmuell_zone),
            ("biomuell", self._biomuell_zone),
            ("altpapier", self._altpapier_zone),
        ):
            mapping = ICS_ZONE_MAPPING[key]
            if zone and zone in mapping:
                do_ids.append(mapping[zone])

        return self.fetch_ics(self.GNR, do_ids)
