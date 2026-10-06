from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

from waste_collection_schedule.exceptions import (
    SourceArgumentException,
)
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def discover_choices(field: str, selections: dict) -> list[tuple[str, str]]:
    """
    Provides the cascading_select choices for affaldonline_dk
    The ``city`` field is populated with every city in a given ``municipality``
    When a ``city`` is selected the ``street`` field is populated with every street in the ``municipality``, filtered to only show ``street``s in the selected ``city``.

    When a ``street`` is selected the house numbers for that ``street`` is gathered.
    This also gives us the ``values`` associated with that address on the affaldonline platform.

    The house number field is called ``values`` for backwards compatibility reasons, as the retired screenscraping approach used this naming convention.
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
        city_list = {
            entry["Bynavn"] for entry in json_entries if entry["Bynavn"] != "0"
        }
        # Sorted, so the dropdown order is stable between config-flow runs.
        return sorted(city_list)
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
            raise SourceArgumentException(
                "values", f"Error from Affaldonline API: {json_content['message']}"
            )
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
