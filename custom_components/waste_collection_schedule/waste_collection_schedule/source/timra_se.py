from datetime import date

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Timrå kommun"
DESCRIPTION = "Source for Timrå kommun (Sweden) waste collection."
URL = "https://www.timra.se"
COUNTRY = "se"
TEST_CASES = {
    "Aspen 195": {"address": "Aspen 195"},
    "Tuna 112": {"address": "Tuna 112"},
    "Torsboda 130": {"address": "Torsboda 130"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the property address exactly as shown on the Timrå kommun "
        "waste collection map (Belägenhetsadress), e.g. 'Aspen 195'. You can "
        "look up the address at https://kartor.timra.se/portal/apps/experiencebuilder/experience/?id=186668f9efeb458c926d85a978fe85de"
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": (
            "Property address as used by Timrå kommun (Belägenhetsadress), "
            "e.g. 'Aspen 195'."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}

ICON_MAP = {
    "Fyrfackskärl 1": Icons.RECYCLING,
    "Fyrfackskärl 2": Icons.GENERAL_WASTE,
}

# The webmap defines which hosted FeatureServer layer currently holds the
# waste collection data. Resolving it dynamically (instead of hardcoding the
# FeatureServer URL, which is suffixed with a publish date and is expected to
# change when Timrå kommun refreshes the schedule for a new year) keeps the
# source working without code changes across those refreshes.
PORTAL_WEBMAP_DATA_URL = (
    "https://kartor.timra.se/portal/sharing/rest/content/items/"
    "f77cab36aa3043d0b9dfeaeb679a23bd/data"
)


def _get_feature_layer_url(session: requests.Session) -> str:
    r = session.get(PORTAL_WEBMAP_DATA_URL, params={"f": "json"}, timeout=30)
    r.raise_for_status()
    layers = r.json().get("operationalLayers", [])
    return str(layers[0]["url"])


def _parse_dates(value: str | None) -> list[date]:
    if not value:
        return []
    year = date.today().year
    dates = []
    for part in value.replace("\r", "").replace("\n", "").split(","):
        part = part.strip()
        if not part:
            continue
        day_str, month_str = part.split("/")
        dates.append(date(year, int(month_str), int(day_str)))
    return dates


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        feature_layer_url = _get_feature_layer_url(session)

        escaped = self._address.replace("'", "''")
        features = self._query(
            session,
            feature_layer_url,
            f"UPPER(beladress) = UPPER('{escaped}')",
            "beladress,karl1,karl2",
        )

        if len(features) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                self._address,
                sorted({f["beladress"] for f in features}),
            )

        if not features:
            similar = self._query(
                session,
                feature_layer_url,
                f"UPPER(beladress) LIKE UPPER('%{escaped}%')",
                "beladress",
            )
            suggestions = sorted({f["beladress"] for f in similar})[:10]
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions
            )

        feature = features[0]

        entries = []
        for d in _parse_dates(feature.get("karl1")):
            entries.append(Collection(d, "Fyrfackskärl 1", ICON_MAP["Fyrfackskärl 1"]))
        for d in _parse_dates(feature.get("karl2")):
            entries.append(Collection(d, "Fyrfackskärl 2", ICON_MAP["Fyrfackskärl 2"]))

        return entries

    @staticmethod
    def _query(
        session: requests.Session, feature_layer_url: str, where: str, out_fields: str
    ) -> list[dict]:
        r = session.get(
            f"{feature_layer_url.rstrip('/')}/query",
            params={
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "false",
                "f": "json",
            },
            timeout=30,
        )
        r.raise_for_status()
        return [f["attributes"] for f in r.json().get("features", [])]
