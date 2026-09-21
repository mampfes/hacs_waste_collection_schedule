from typing import TYPE_CHECKING, Any

import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

CLIENT_ID_LOOKUP = {
    "aeroe": "db765a2f-3f50-4abd-a738-3825813fedcb",
    "assens": "afd912a2-44b3-402f-9e13-5aeb701ce143",
    "favrskov": "dffcc5b6-b9ee-478d-82e2-030123485f7e",
    "fanoe": "af7badab-508b-43fa-87dc-162347b288f3",
    "fredericia": "dea6ff86-2ee9-4e7a-8fce-76dcb5625714",
    "ffv": "ceca5978-6380-4ff8-ac28-9b6505457da8",
    "holbaek": "017efd06-ac42-4b36-8a70-ab309162e988",
    "langeland": "be8a9420-a9ae-42e6-83f2-eda5ec3fa29f",
    "middelfart": "17F02B8B-7743-4FA6-8646-74F59436AED1",
    "morsoe": "0199b7d2-bbae-46a5-a726-293c9236f4e5",
    "nyborg": "4571D02F-602C-485A-8961-466EAA2B7B04",
    "silkeborg": "eea63ff1-96fd-4288-b96e-83100ebbc378",
    "rebild": "cb3ddc8c-900a-43ce-ac88-ec7587db4db3",
    "vejle": "209cb669-e2e8-4c9b-8048-8287db51a61e",
    "viborg": "4EBB900C-088E-475F-83ED-B087F4AD07BA",
}


def discover_choices(field: str, selections: dict) -> list[tuple[str, str]]:
    """
    Provides the cascading_select choices for affaldonline_dk
    The ``city`` field is populated with every city in a given ``municipality``
    When a ``city`` is selected the ``street`` field is populated with every street in the ``municipality``, filtered to only show ``street``s in the selected ``city``.

    When a ``street`` is selected the house numbers for that ``street`` is gathered.
    This also gives us the ``values`` associated with that address on the affaldonline platform.

    The house number field is called ``values`` for backwards compatability reasons, as the retired screenscraping approach used this naming convention.
    By keeping that naming scheme old installations can continue working.

    The ``values`` field is labeled with the house numbers, while the value is the internal affaldonline identifier string for that address.
    """
    municipality = selections.get("municipality")
    if not municipality:
        return []
    session = cffi_requests.Session(impersonate="chrome")
    if field == "city":
        response = session.get(
            url=f"https://www.affaldonline.dk/kalender/{municipality}/acCal.php?term="
        )
        if response.status_code != 200:
            return []
        json_entries = response.json()
        city_list = [(entry["Bynavn"]) for entry in json_entries if entry["Bynavn"] != "0"]
        return list(set(city_list))
    if field == "street":
        response = session.get(
            url=f"https://www.affaldonline.dk/kalender/{municipality}/acCal.php?term="
        )
        if response.status_code != 200:
            return []
        json_entries = response.json()

        city = selections.get("city")
        street_list = [
            (
                entry["vejnavn"],
                f"{entry['vejnavn']}|{entry['postnr']}|{entry['Bynavn']}",
            )
            for entry in json_entries
            if not city or entry["Bynavn"] == city
        ]
        return street_list
    if field == "values":
        street = selections.get("street")
        if not street:
            return []
        # Split the street string into the three values the api expects
        street_components = street.split("|")
        response = session.get(
            url=f"https://www.affaldonline.dk/kalender/{municipality}/husnrCal.php",
            params={
                "vejnavn": street_components[0],
                "postnr": street_components[1],
                "postdist": street_components[2],  # This is the municipality name
            },
        )
        # The response is quite strange, it is a html select element...
        soup = BeautifulSoup(response.text, "html.parser")
        options = soup.find_all("option")
        return [(str(option.string), str(option["value"])) for option in options]
    return []


class AffaldOnlineDkRetriver(RetrieverFunc):
    """
    Calls the undocumented affaldonline api.
    The api differenciates municipalities by the "X-Client-Provider" header.
    Suitable provider_id's are available in the CLIENT_ID_LOOKUP map.

    Reads the fields ``municipality`` and ``values`` from the source params.
    The ``values`` param is an internal identifying string used by affaldonline.
    It is found using the cascading select implemented in ``get_choices`` above
    """

    def __call__(self, source: "BaseSource") -> dict[str, Any]:
        municipality = source.params.get("municipality")
        if not municipality:
            raise SourceArgumentException(
                "municipality", "Provided munipality is not valid"
            )
        client_id = CLIENT_ID_LOOKUP.get(municipality)
        if not client_id:
            raise SourceArgumentException(
                "municipality", "Provided munipality is not valid"
            )
        values = source.params.get("values")
        if not values:
            raise SourceArgumentException("values", "Internal values are missing")
        address_id_split = values.split("|")
        if len(address_id_split) < 2:
            raise SourceArgumentException("values", "Provided address is not valid")
        address_id = "|".join(address_id_split[-2:])
        return source.session.get(
            url="https://www.affaldonline.dk/api/address/collections",
            params={"groupBy": "date", "addressId": address_id},
            headers={
                "X-Client-Type": "Kunde app",
                "X-Client-OS": "android",
                "X-Client-Version": "9999",
                "X-Client-Provider": client_id,
            },
        )


class AffaldOnlineDkParser(Parser["list[dict]"]):
    """
    Parses the affaldonline data into [{date, fraction_name, fraction_types:[fraction_id]}] records
    If source params provides the "split_bins" boolean, the records is split into multiple records, one for each fraction_id
    """

    def __call__(
        self, response: requests.Response, source: "BaseSource | None" = None
    ) -> "list[dict]":
        json_content = response.json()
        if "message" in json_content:
            raise ValueError("Error from API: " + json_content["message"])
        entries = []
        for entry in json_content:
            for collection in entry["collections"]:
                fraction_name = str(collection["fraction"]["name"]).strip()
                if source and source.params.get("split_bins", False):
                    # Split the fractions into individual collections
                    for fraction_id in collection["daIcon"]:
                        entries.append(
                            {
                                "date": entry["date"],
                                "fraction_name": fraction_name,
                                "fraction_types": [fraction_id],
                            }
                        )
                else:
                    entries.append(
                        {
                            "date": entry["date"],
                            "fraction_name": fraction_name,
                            "fraction_types": collection["daIcon"],
                        }
                    )
        return entries
