import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Fredrikstad kommune"
DESCRIPTION = "Source for Fredrikstad kommune waste collection."
URL = "https://www.fredrikstad.kommune.no"
TEST_CASES = {
    "Kanelveien 4": {"address": "Kanelveien 4"},
}

BASE_URL = "https://arcgis.fredrikstad.kommune.no/server/rest/services/Renovasjon/MinRenovasjon/MapServer"
SCHEDULE_DAYS = 365


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        waste_types = _get_waste_types(session)
        avt_lnr = self._get_avt_lnr(session)

        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=SCHEDULE_DAYS)

        r = session.get(
            f"{BASE_URL}/1/query",
            params={
                "f": "json",
                "orderByFields": "Dato",
                "outFields": "Dato,AvfallId",
                "returnGeometry": "false",
                "spatialRel": "esriSpatialRelIntersects",
                "where": (
                    f"AvtLnr = {avt_lnr} "
                    f"AND Dato >= date '{today.isoformat()}' "
                    f"AND Dato <= date '{end_date.isoformat()}'"
                ),
            },
        )
        r.raise_for_status()

        entries = []
        for feature in r.json().get("features", []):
            attr = feature["attributes"]
            epoch_ms = attr["Dato"]
            avfall_id = attr["AvfallId"]
            collection_date = datetime.date.fromtimestamp(epoch_ms / 1000)
            waste_name = waste_types.get(avfall_id, f"Avfall {avfall_id}")
            entries.append(Collection(date=collection_date, t=waste_name))

        return entries

    def _get_avt_lnr(self, session: requests.Session) -> int:
        r = session.get(
            f"{BASE_URL}/0/query",
            params={
                "f": "json",
                "outFields": "AvtLnr",
                "returnGeometry": "false",
                "spatialRel": "esriSpatialRelIntersects",
                "where": f"UPPER(Adresse) = '{self._address.upper()}' AND AvtStatus = 0",
            },
        )
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            raise ValueError(f"Address not found: {self._address}")
        return features[0]["attributes"]["AvtLnr"]


def _get_waste_types(session: requests.Session) -> dict[int, str]:
    """Return AvfallId → name mapping from the layer's coded value domain."""
    r = session.get(f"{BASE_URL}/1", params={"f": "json"})
    r.raise_for_status()
    for field in r.json().get("fields", []):
        if field["name"] == "AvfallId":
            domain = field.get("domain") or {}
            if domain.get("type") == "codedValue":
                return {cv["code"]: cv["name"] for cv in domain["codedValues"]}
    return {}
