import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Affaldonline"
DESCRIPTION = "Gather waste collection schedules from Affaldonline"
URL = "https://affaldonline.dk"
API_URL = "https://www.affaldonline.dk/api/address/collections?groupBy=date&addressId={values}"

SOURCE_CODEOWNERS = ["@superrob"]

_LOGGER = logging.getLogger("waste_collection_schedule.affaldonline_dk")

# AffaldOnline is extremely random with their naming, which can vary even in the same municipality.
ICON_MAP = {
    # Residual / residual+food rounds
    "Rest/Mad": Icons.GENERAL_WASTE,
    "Mad/Rest": Icons.GENERAL_WASTE,
    "Rest/mad": Icons.GENERAL_WASTE,
    "Rest-/madaffald": Icons.GENERAL_WASTE,
    "Restaffald": Icons.GENERAL_WASTE,
    "Dagrenovation": Icons.GENERAL_WASTE,
    # Food / organic
    "Bioaffald": Icons.BIO_KITCHEN,
    "Haveaffald": Icons.GARDEN,
    # Paper and cardboard, alone or combined with glass/metal
    "Pap": Icons.PAPER,
    "Papir/Pap": Icons.PAPER,
    "Pap/Papir": Icons.PAPER,
    "PPGM": Icons.RECYCLING,
    "Papir/Pap/Glas": Icons.RECYCLING,
    "Papir/Pap og tekstil": Icons.RECYCLING,
    "Papir/Pap-Metal/Glas": Icons.RECYCLING,
    "Papir/Pap og Plast/Mad- og drikkekartoner": Icons.RECYCLING,
    "Papir/småt pap og glas/metal": Icons.RECYCLING,
    "Pap/papir og glas/metal": Icons.RECYCLING,
    # Glass and metal
    "Glas og metal": Icons.GLASS,
    # Plastic and beverage cartons (MDK = mad-/drikkekartoner)
    "PMDK": Icons.PLASTIC_PACKAGING,
    "Plast/Drikkekarton": Icons.PLASTIC_PACKAGING,
    "Plast/Drikkekarton/Metal": Icons.PLASTIC_PACKAGING,
    "Plast/fødevarekarton": Icons.PLASTIC_PACKAGING,
    "Plast + Mad-/Drikkekartoner": Icons.PLASTIC_PACKAGING,
    "Plast/mad- og drikkekartoner og glas/metal": Icons.PLASTIC_PACKAGING,
    "Metal/Glas/Plast/MDK": Icons.RECYCLING,
    # Mixed recyclables
    "Genbrug": Icons.RECYCLING,
    "Genanvendeligt": Icons.RECYCLING,
    # Everything else
    "Storskrald": Icons.BULKY,
    "Miljøkasse": Icons.HAZARDOUS,
    "Røde kasser": Icons.HAZARDOUS,
    "Tekstilaffald": Icons.TEXTILE,
}

# Maps abbreviations into more readable texts.
TYPE_MAP = {
    "PMDK": "Plast og Drikkekartoner",
    "PPGM": "Pap/Papir og Glas/Metal",
}

AFFALDONLINE_MUNICIPALITIES = {
    "aeroe": {
        "title": "Ærø Kommune",
        "url": "https://www.aeroekommune.dk/",
        "values": "Nørregade|1||||5970|Ærøskøbing|1228262|448776|0",
        "client": "db765a2f-3f50-4abd-a738-3825813fedcb",
    },
    "assens": {
        "title": "Assens Forsyning",
        "url": "https://www.assensforsyning.dk/",
        "values": "Vandværksvej|2||||5560|Aarup|11266|456952|0",
        "client": "afd912a2-44b3-402f-9e13-5aeb701ce143",
    },
    "favrskov": {
        "title": "Favrskov Forsyning",
        "url": "https://www.favrskovforsyning.dk",
        "values": "Nørregade|1||||8382|Hinnerup|6443|108156|0",
        "client": "dffcc5b6-b9ee-478d-82e2-030123485f7e",
    },
    "fanoe": {
        "title": "Fanø Kommune",
        "url": "https://fanoe.dk/",
        "values": "Nørre Klit|5||||6720|Fanø|2582|1747246|0",
        "client": "af7badab-508b-43fa-87dc-162347b288f3",
    },
    "fredericia": {
        "title": "Fredericia Kommune Affald & Genbrug",
        "url": "https://affaldgenbrug-fredericia.dk/",
        "values": "Nørre Allé|5||||7000|Fredericia|11079971|1907927|0",
        "client": "dea6ff86-2ee9-4e7a-8fce-76dcb5625714",
    },
    "ffv": {
        "title": "Faaborg Forsynings Virksomhed",
        "url": "https://www.ffv.dk/",
        "values": "Marsk Billesvej|18||||5672|Broby|36193544|576846|0",
        "client": "ceca5978-6380-4ff8-ac28-9b6505457da8",
    },
    "holbaek": {
        "title": "Fors (Holbæk)",
        "url": "https://www.fors.dk/",
        "values": "Østerled|5||||4300|Holbæk|28441|1081575|2055",
        "client": "017efd06-ac42-4b36-8a70-ab309162e988",
    },
    "langeland": {
        "title": "Langeland Forsyning",
        "url": "https://www.langeland-forsyning.dk/",
        "values": "Nørregade|1||||5900|Rudkøbing|3535|383566|0",
        "client": "be8a9420-a9ae-42e6-83f2-eda5ec3fa29f",
    },
    "middelfart": {
        "title": "Middelfart Kommune",
        "url": "https://middelfart.dk/",
        "values": "Nørregade|2||||5592|Ejby|11288085|6496420|0",
        "client": "17F02B8B-7743-4FA6-8646-74F59436AED1",
    },
    "morsoe": {
        "title": "Morsø Kommune",
        "url": "https://mors.dk/",
        "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        "client": "0199b7d2-bbae-46a5-a726-293c9236f4e5",
    },
    "nyborg": {
        "title": "Nyborg Forsyning & Service A/S",
        "url": "https://www.nfs.as/",
        "values": "Nørregade|5||||5800|Nyborg|8896288|552542|0",
        "client": "4571D02F-602C-485A-8961-466EAA2B7B04",
    },
    "silkeborg": {
        "title": "Silkeborg Forsyning",
        "url": "https://www.silkeborgforsyning.dk/",
        "values": "Nørregade|5||||8620|Kjellerup|45814316|1291964|0",
        "client": "eea63ff1-96fd-4288-b96e-83100ebbc378",
    },
    # Sorø is NOT available on the API. But was also not available on the old codebase either
    "soroe": {
        "title": "Sorø Kommune",
        "url": "https://soroe.dk/",
        "values": "Nørrevej|4| |||4180|Sorø|8569|8838|0|0",
    },
    "rebild": {
        "title": "Rebild Kommune",
        "url": "https://rebild.dk/",
        "values": "Nørregade|1||||9500|Hobro|11634418|19222228|0",
        "client": "cb3ddc8c-900a-43ce-ac88-ec7587db4db3",
    },
    "vejle": {
        "title": "Vejle Kommune",
        "url": "https://www.vejle.dk/",
        "values": "Nørregade|11||||7100|Vejle|16518799|16518799|0",
        "client": "209cb669-e2e8-4c9b-8048-8287db51a61e",
    },
    "viborg": {
        "title": "Revas (Viborg Kommune)",
        "url": "https://www.revas.dk/",
        "values": "Hjultorvet|1||||8800|Viborg|8228245|8739|0",
        "client": "4EBB900C-088E-475F-83ED-B087F4AD07BA",
    },
}

EXTRA_INFO = [
    {
        "title": info["title"],
        "url": info["url"],
        "default_params": {"municipality": municipality},
    }
    for municipality, info in AFFALDONLINE_MUNICIPALITIES.items()
    if "client" in info
]


def select_test_cases(municipalities):
    test_cases = {}
    for name, info in municipalities.items():
        if "client" in info:
            test_cases[name] = {"municipality": name, "values": info["values"]}

    return test_cases


# Dynamically generate TEST_CASES from the AFFALDONLINE_MUNICIPALITIES dictionary
TEST_CASES = select_test_cases(AFFALDONLINE_MUNICIPALITIES)


class Source:
    def __init__(self, municipality: str, values: str):
        _LOGGER.debug(
            "Initializing Source with municipality=%s, values=%s",
            municipality,
            values,
        )

        # Gather the address id from the raw values
        # The address id is the last two values in the raw values string
        address_id_split = values.split("|")
        if len(address_id_split) < 2:
            raise SourceArgumentException("values", "Provided values is not valid")
        address_id = "|".join(address_id_split[-2:])

        self._api_url = API_URL.format(values=address_id)
        self._client_provider = AFFALDONLINE_MUNICIPALITIES.get(municipality, {}).get(
            "client", ""
        )
        if self._client_provider == "":
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                municipality,
                [
                    key
                    for key, info in AFFALDONLINE_MUNICIPALITIES.items()
                    if "client" in info
                ],
            )
        self._client_provider = str(self._client_provider)

    def fetch(self) -> list[Collection]:
        _LOGGER.debug("Fetching data from %s", self._api_url)

        entries: list[Collection] = []
        response = requests.get(
            self._api_url,
            headers={
                "X-Client-Provider": self._client_provider,
                "X-Client-Type": "Kunde app",
                "X-Client-OS": "android",
                "X-Client-Version": "9999",  # Needs to be higher than the current version.
            },
            timeout=10,
        )
        json_content = response.json()

        if "message" in json_content:
            raise ValueError("Error from API: " + json_content["message"])

        for entry in json_content:
            for collection in entry["collections"]:
                fraction_name = str(collection["fraction"]["name"]).strip()
                entries.append(
                    Collection(
                        date=datetime.strptime(entry["date"], "%Y-%m-%d").date(),
                        t=TYPE_MAP.get(fraction_name, fraction_name),
                        icon=ICON_MAP.get(fraction_name, Icons.GENERAL_WASTE),
                    )
                )

        return entries
