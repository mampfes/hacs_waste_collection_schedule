import logging
from typing import ClassVar

from bs4 import BeautifulSoup
from waste_collection_schedule import (  # type: ignore[attr-defined]
    Collection,
    Icons,
    date_parsers,
    field_terms,
    regions,
)
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    cascading_select,
    municipality,
    boolean
)
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
)

_LOGGER = logging.getLogger("waste_collection_schedule.affaldonline_dk")

""" 
Waste seperation in Denmark is mandetory to be atleast seperated into these 10 fractions:
Food Waste
Paper
Cardboard
Plastic
Food and drink cartons
Metal
Glass
Textiles
Hazardous waste
Residual waste

Only 6 out of the 10 types currently have a WasteType, the following are missing:
Cardboard, Plastic, Food and drink cartons, Metal

These 10 fractions are usually combined into bins for collection, with one or two compartments. 
Some fractions are additionally allowed to be combined into the same compartment. As such some bins have 4 different fractions combined.

This makes the WasteType approach highly impractical, as some bins would end up with the same WasteType, even though it is a completely different bin and content.
For example take these two bins:
Metal, Glass, Paper & Cardboard
Plastic & Food and drink cartons

Both of these would under the current WasteType system end up as WasteType.RECYCLING, making for a confusing UX.

Instead the source currently uses the older direct Collection system, which offers more flexibility.
The API contains the exact fractions from each collection, and thus is able to dynamically name every collection based on the fraction content.
Additionally, if the user so desires, the param "split_bins" can be set. This splits each collection into separate collections, one for each fraction.
"""

"""
Maps fraction ID's to text and icon.
There are 90 fractions, however most are only used at recycling stations.
"""
FRACTION_MAP = {
    19: ("Elektronik", Icons.ELECTRONICS),
    27: ("Farligt affald", Icons.HAZARDOUS),
    41: ("Genbrug", Icons.RECYCLING),
    43: ("Madaffald", Icons.BIO_KITCHEN),
    46: ("Glas", Icons.GLASS),
    47: ("Papir", Icons.PAPER),
    50: ("Drikkedåser", Icons.METAL),
    51: ("Metal", Icons.METAL),
    53: ("Metal", Icons.METAL),
    54: ("Haveaffald", Icons.GARDEN),
    58: ("Pap", Icons.PAPER),
    59: ("Kartoner", Icons.PLASTIC_PACKAGING),
    72: ("Plast", Icons.PLASTIC_PACKAGING),
    78: ("Restaffald", Icons.GENERAL_WASTE),
    80: ("Restaffald", Icons.GENERAL_WASTE),
    81: ("Storskrald", Icons.BULKY),
    88: ("Tekstiler", Icons.TEXTILE),
    89: ("Madaffald", Icons.BIO_KITCHEN),
}

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


class Source(BaseSource):
    TITLE = "Affaldonline"
    DESCRIPTION = "Gather waste collection schedules from Affaldonline"
    URL = "https://affaldonline.dk"
    API_URL = "https://www.affaldonline.dk/api/address/collections"
    SOURCE_CODEOWNERS = ["@superrob"]

    REGIONS = regions.from_yaml(
        "affaldonline_dk", title_suffix="affaldonline"
    )

    TEST_CASES: ClassVar[dict] = {
        "aeroe": {
            "municipality": "aeroe",
            "street": "Nørregade|5970|Ærøskøbing",
            "values": "Nørregade|1||||5970|Ærøskøbing|1228262|448776|0",
        },
        "assens": {
            "municipality": "assens",
            "street": "Vandværksvej|5560|Aarup",
            "values": "Vandværksvej|2||||5560|Aarup|11266|456952|0",
        },
        "favrskov": {
            "municipality": "favrskov",
            "street": "Nørregade|8382|Hinnerup",
            "values": "Nørregade|1||||8382|Hinnerup|6443|108156|0",
        },
        "fanoe": {
            "municipality": "fanoe",
            "street": "Nørre Klit|6720|Fanø",
            "values": "Nørre Klit|5||||6720|Fanø|2582|1747246|0",
        },
        "fredericia": {
            "municipality": "fredericia",
            "street": "Nørre Allé|7000|Fredericia",
            "values": "Nørre Allé|5||||7000|Fredericia|11079971|1907927|0",
        },
        "ffv": {
            "municipality": "ffv",
            "street": "Marsk Billesvej|5672|Broby",
            "values": "Marsk Billesvej|18||||5672|Broby|36193544|576846|0",
        },
        "holbaek": {
            "municipality": "holbaek",
            "street": "Østerled|4300|Holbæk",
            "values": "Østerled|5||||4300|Holbæk|28441|1081575|2055",
        },
        "langeland": {
            "municipality": "langeland",
            "street": "Nørregade|5900|Rudkøbing",
            "values": "Nørregade|1||||5900|Rudkøbing|3535|383566|0",
        },
        "middelfart": {
            "municipality": "middelfart",
            "street": "Nørregade|5592|Ejby",
            "values": "Nørregade|2||||5592|Ejby|11288085|6496420|0",
        },
        "morsoe": {
            "municipality": "morsoe",
            "street": "Østervang|7900|Nykøbing M",
            "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        },
        "morsoe_split": {
            "municipality": "morsoe",
            "split_bins": True,
            "street": "Østervang|7900|Nykøbing M",
            "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        },
        "nyborg": {
            "municipality": "nyborg",
            "street": "Nørregade|5800|Nyborg",
            "values": "Nørregade|5||||5800|Nyborg|8896288|552542|0",
        },
        "silkeborg": {
            "municipality": "silkeborg",
            "street": "Nørregade|8620|Kjellerup",
            "values": "Nørregade|5||||8620|Kjellerup|45814316|1291964|0",
        },
        "rebild": {
            "municipality": "rebild",
            "street": "Nørregade|9500|Hobro",
            "values": "Nørregade|1||||9500|Hobro|11634418|19222228|0",
        },
        "vejle": {
            "municipality": "vejle",
            "values": "Nørregade|11||||7100|Vejle|16518799|16518799|0",
        },
        "viborg": {
            "municipality": "viborg",
            "street": "Hjultorvet|8800|Viborg",
            "values": "Hjultorvet|1||||8800|Viborg|8228245|8739|0",
        },
    }

    RAISE_ON_EMPTY = True
    PARAMS = (
        municipality("municipality"),
        boolean("split_bins", "Split bins into fractions"),
        cascading_select(
            ("street", field_terms.STREET),
            ("values", field_terms.HOUSE_NUMBER),
        ),
    )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Options for one cascade level given the levels chosen so far."""
        municipality = selections.get("municipality")
        if not municipality:
            _LOGGER.warning("No municipality selected")
            return []
        from curl_cffi import requests as cffi_requests

        session = cffi_requests.Session(impersonate="chrome")
        if field == "street":
            response = session.get(
                url=f"https://www.affaldonline.dk/kalender/{municipality}/acCal.php?term="
            )
            if response.status_code != 200:
                return []
            json_entries = response.json()
            street_list = [
                (
                    entry["value"],
                    f"{entry['vejnavn']}|{entry['postnr']}|{entry['Bynavn']}",
                )
                for entry in json_entries
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

    def retrieve(self, source):
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

    def parse(self, response, source):
        json_content = response.json()
        if "message" in json_content:
            raise ValueError("Error from API: " + json_content["message"])

        entries = []
        for entry in json_content:
            for collection in entry["collections"]:
                fraction_name = str(collection["fraction"]["name"]).strip()
                if self.params.get("split_bins", False):
                    # Split the fractions into individual collections
                    for fraction_id in collection["daIcon"]:
                        entries.append({"date": entry["date"], "fraction_name": fraction_name, "fraction_types": [fraction_id]})
                else:
                    entries.append({"date": entry["date"], "fraction_name": fraction_name, "fraction_types": collection["daIcon"]})
        return entries

    # Yes, under the new WasteTypes paradime, this is "wrong".
    # However the alternative would be both breaking and in many cases group multiple different containers into the same category.
    def classify(self, record):
        parse_date = date_parsers.for_format("%Y-%m-%d")
        date = parse_date(record["date"])
        if not date:
            return None
        if not record["fraction_name"]:
            return None
        fraction_names = []
        fraction_icon = Icons.GENERAL_WASTE
        for fraction_id in record["fraction_types"]:
            fraction_info = FRACTION_MAP.get(fraction_id, (f"{fraction_id} Mangler navn", Icons.GENERAL_WASTE))    
            fraction_names.append(fraction_info[0])
            fraction_icon = fraction_info[1]
        return Collection(
            date=date,
            t=fraction_names[0] if len(fraction_names) == 1 else " og ".join([", ".join(fraction_names[:-1]),fraction_names[-1]]),
            icon=fraction_icon,
        )

    """     
    This is the unused transformer aproach. Due to waste_type overlap.
    transform = JsonTransformer(
        date_key="date", 
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_key="type",
        description_key="type",
        type_value_map=TYPE_MAP,
        carry_raw_label=True,
    ) """
