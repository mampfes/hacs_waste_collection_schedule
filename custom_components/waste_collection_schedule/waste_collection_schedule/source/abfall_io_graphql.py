import datetime
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AbfallIOGraphQL import SERVICE_MAP

TITLE = "Abfall.IO / AbfallPlus (GraphQL)"
DESCRIPTION = "Source for AbfallPlus.de waste collection using the v3 GraphQL API."
URL = "https://www.abfallplus.de"
COUNTRY = "de"

_LOGGER = logging.getLogger(__name__)

INIT_URL = "https://api.abfall.io"
GQL_URL = "https://widgets.abfall.io/graphql"
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
}

APPOINTMENTS_QUERY = """
query Query($idHouseNumber: ID!, $wasteTypes: [ID], $dateMin: Date, $dateMax: Date, $showInactive: Boolean) {
    appointments(idHouseNumber: $idHouseNumber, wasteTypes: $wasteTypes, dateMin: $dateMin, dateMax: $dateMax, showInactive: $showInactive) {
        date
        wasteType {
            name
        }
    }
}
"""


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": s["url"],
            "default_params": {"key": s["service_id"]},
        }
        for s in SERVICE_MAP
    ]


TEST_CASES = {
    "Altlandsberg": {
        "key": "efb75cbd1f08fae1d4e47ae72a85c655",
        "idHouseNumber": 4136,
    },
    "Strausberg": {
        "key": "efb75cbd1f08fae1d4e47ae72a85c655",
        "idHouseNumber": 5985,
    },
}


class Source:
    def __init__(self, key, idHouseNumber, wasteTypes=None):
        self._key = key
        self._id_house_number = str(idHouseNumber)
        self._waste_types = [str(w) for w in wasteTypes] if wasteTypes else None

    def fetch(self):
        r = requests.get(INIT_URL, params={"key": self._key}, headers=HEADERS)
        if r.status_code == 401:
            raise ValueError(
                f"API key '{self._key}' is not valid for the abfall.io v3 GraphQL API. "
                "Please check that you are using the correct key for your provider."
            )
        r.raise_for_status()
        config = r.json()
        api_key = config["apiKey"]

        waste_types = self._waste_types
        if waste_types is None:
            waste_types = [
                wt["wasteType"]
                for wt in config["settings"].get("PUB_ABFALLTYPEN", [])
                if wt.get("checked", False)
            ]

        now = datetime.date.today()
        date_max = now + datetime.timedelta(days=365)

        gql_headers = {
            **HEADERS,
            "Content-Type": "application/json",
            "x-abfallplus-api-key": api_key,
        }

        r = requests.post(
            GQL_URL,
            json={
                "query": APPOINTMENTS_QUERY,
                "variables": {
                    "idHouseNumber": self._id_house_number,
                    "wasteTypes": waste_types if waste_types else None,
                    "dateMin": now.isoformat(),
                    "dateMax": date_max.isoformat(),
                    "showInactive": False,
                },
            },
            headers=gql_headers,
        )
        r.raise_for_status()

        data = r.json()
        if "errors" in data:
            raise ValueError(f"GraphQL error: {data['errors']}")

        entries = []
        for apt in data.get("data", {}).get("appointments", []):
            date = datetime.date.fromisoformat(apt["date"])
            waste_type = apt["wasteType"]["name"]
            entries.append(Collection(date, waste_type))

        return entries
