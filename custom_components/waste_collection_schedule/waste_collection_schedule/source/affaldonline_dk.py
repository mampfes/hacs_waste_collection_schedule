from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, text_field
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# Every municipality shares one API; the client id selects the waste company.
MUNICIPALITIES = {
    "aeroe": {
        "title": "Ærø Kommune",
        "url": "https://www.aeroekommune.dk/",
        "client": "db765a2f-3f50-4abd-a738-3825813fedcb",
    },
    "assens": {
        "title": "Assens Forsyning",
        "url": "https://www.assensforsyning.dk/",
        "client": "afd912a2-44b3-402f-9e13-5aeb701ce143",
    },
    "favrskov": {
        "title": "Favrskov Forsyning",
        "url": "https://www.favrskovforsyning.dk",
        "client": "dffcc5b6-b9ee-478d-82e2-030123485f7e",
    },
    "fanoe": {
        "title": "Fanø Kommune",
        "url": "https://fanoe.dk/",
        "client": "af7badab-508b-43fa-87dc-162347b288f3",
    },
    "fredericia": {
        "title": "Fredericia Kommune Affald & Genbrug",
        "url": "https://affaldgenbrug-fredericia.dk/",
        "client": "dea6ff86-2ee9-4e7a-8fce-76dcb5625714",
    },
    "ffv": {
        "title": "Faaborg Forsynings Virksomhed",
        "url": "https://www.ffv.dk/",
        "client": "ceca5978-6380-4ff8-ac28-9b6505457da8",
    },
    "holbaek": {
        "title": "Fors (Holbæk)",
        "url": "https://www.fors.dk/",
        "client": "017efd06-ac42-4b36-8a70-ab309162e988",
    },
    "langeland": {
        "title": "Langeland Forsyning",
        "url": "https://www.langeland-forsyning.dk/",
        "client": "be8a9420-a9ae-42e6-83f2-eda5ec3fa29f",
    },
    "middelfart": {
        "title": "Middelfart Kommune",
        "url": "https://middelfart.dk/",
        "client": "17F02B8B-7743-4FA6-8646-74F59436AED1",
    },
    "morsoe": {
        "title": "Morsø Kommune",
        "url": "https://mors.dk/",
        "client": "0199b7d2-bbae-46a5-a726-293c9236f4e5",
    },
    "nyborg": {
        "title": "Nyborg Forsyning & Service A/S",
        "url": "https://www.nfs.as/",
        "client": "4571D02F-602C-485A-8961-466EAA2B7B04",
    },
    "silkeborg": {
        "title": "Silkeborg Forsyning",
        "url": "https://www.silkeborgforsyning.dk/",
        "client": "eea63ff1-96fd-4288-b96e-83100ebbc378",
    },
    "rebild": {
        "title": "Rebild Kommune",
        "url": "https://rebild.dk/",
        "client": "cb3ddc8c-900a-43ce-ac88-ec7587db4db3",
    },
    "vejle": {
        "title": "Vejle Kommune",
        "url": "https://www.vejle.dk/",
        "client": "209cb669-e2e8-4c9b-8048-8287db51a61e",
    },
    "viborg": {
        "title": "Revas (Viborg Kommune)",
        "url": "https://www.revas.dk/",
        "client": "4EBB900C-088E-475F-83ED-B087F4AD07BA",
    },
}


def _address_id(values: str) -> str:
    # The address id is the last two values of the raw "|"-separated string.
    parts = values.split("|")
    if len(parts) < 2:
        raise SourceArgumentException("values", "Provided values is not valid")
    return "|".join(parts[-2:])


def _fraction(record: dict) -> str:
    return str(record["collection"]["fraction"]["name"])


@final
class Source(BaseSource):
    TITLE = "Affaldonline"
    DESCRIPTION = "Gather waste collection schedules from Affaldonline"
    URL = "https://affaldonline.dk"
    COUNTRY = "dk"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@superrob"]
    RAISE_ON_EMPTY = True

    REGIONS = tuple(
        region(info["title"], url=info["url"], municipality=key)
        for key, info in MUNICIPALITIES.items()
    )

    TEST_CASES: ClassVar[dict] = {
        "aeroe": {
            "municipality": "aeroe",
            "values": "Nørregade|1||||5970|Ærøskøbing|1228262|448776|0",
        },
        "assens": {
            "municipality": "assens",
            "values": "Vandværksvej|2||||5560|Aarup|11266|456952|0",
        },
        "favrskov": {
            "municipality": "favrskov",
            "values": "Nørregade|1||||8382|Hinnerup|6443|108156|0",
        },
        "fanoe": {
            "municipality": "fanoe",
            "values": "Nørre Klit|5||||6720|Fanø|2582|1747246|0",
        },
        "fredericia": {
            "municipality": "fredericia",
            "values": "Nørre Allé|5||||7000|Fredericia|11079971|1907927|0",
        },
        "ffv": {
            "municipality": "ffv",
            "values": "Marsk Billesvej|18||||5672|Broby|36193544|576846|0",
        },
        "holbaek": {
            "municipality": "holbaek",
            "values": "Østerled|5||||4300|Holbæk|28441|1081575|2055",
        },
        "langeland": {
            "municipality": "langeland",
            "values": "Nørregade|1||||5900|Rudkøbing|3535|383566|0",
        },
        "middelfart": {
            "municipality": "middelfart",
            "values": "Nørregade|2||||5592|Ejby|11288085|6496420|0",
        },
        "morsoe": {
            "municipality": "morsoe",
            "values": "Østervang|1||||7900|Nykøbing M|8970056|1719615|0",
        },
        "nyborg": {
            "municipality": "nyborg",
            "values": "Nørregade|5||||5800|Nyborg|8896288|552542|0",
        },
        "silkeborg": {
            "municipality": "silkeborg",
            "values": "Nørregade|5||||8620|Kjellerup|45814316|1291964|0",
        },
        "rebild": {
            "municipality": "rebild",
            "values": "Nørregade|1||||9500|Hobro|11634418|19222228|0",
        },
        "vejle": {
            "municipality": "vejle",
            "values": "Nørregade|11||||7100|Vejle|16518799|16518799|0",
        },
        "viborg": {
            "municipality": "viborg",
            "values": "Hjultorvet|1||||8800|Viborg|8228245|8739|0",
        },
    }

    PARAMS = (
        dropdown("municipality", list(MUNICIPALITIES)),
        text_field("values", "Values"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the address search of your waste company on the AffaldOnline "
            "platform, select your address and copy the raw `values` string of the "
            "address (pipe separated, e.g. `Nørregade|1||||5970|Ærøskøbing|1228262|448776|0`). "
            "Use the municipality key of your waste company as `municipality`."
        ),
        "da": (
            "Find din adresse i adressesøgningen hos dit affaldsselskab paa "
            "AffaldOnline og kopier adressens `values`-streng (adskilt af |). "
            "Brug nøglen for dit affaldsselskab som `municipality`."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.TEXTILES,
        wt.OTHER,
    ]

    retrieve = HttpGetRetriever(
        url="https://www.affaldonline.dk/api/address/collections",
        params=lambda values, **_: {
            "groupBy": "date",
            "addressId": _address_id(values),
        },
        headers=lambda municipality, **_: {
            "X-Client-Provider": MUNICIPALITIES[municipality]["client"],
            "X-Client-Type": "Kunde app",
            "X-Client-OS": "android",
            "X-Client-Version": "9999",  # Needs to be higher than the current version.
        },
    )
    parse = JsonParser()
    preprocess = ExplodeList("collections", into="collection")
    # AffaldOnline is extremely random with its naming, which can vary even
    # within one municipality.
    transform = JsonTransformer(
        date_key="date",
        type_key=_fraction,
        carry_raw_label=True,
        type_value_map={
            # Residual / residual+food rounds
            "Rest/Mad": wt.GENERAL_WASTE,
            "Mad/Rest": wt.GENERAL_WASTE,
            "Rest-/madaffald": wt.GENERAL_WASTE,
            "Restaffald": wt.GENERAL_WASTE,
            "Dagrenovation": wt.GENERAL_WASTE,
            # Food / garden
            "Bioaffald": wt.FOOD_WASTE,
            "Haveaffald": wt.GARDEN_WASTE,
            # Paper and cardboard alone
            "Pap": wt.PAPER,
            "Papir/Pap": wt.PAPER,
            "Pap/Papir": wt.PAPER,
            # Glass and metal
            "Glas og metal": wt.GLASS,
            "Glas/Metal": wt.GLASS,
            # Combined and mixed recyclables, plastic and beverage cartons
            # (PMDK = plast + mad-/drikkekartoner, PPGM = pap/papir + glas/metal)
            "PMDK": wt.RECYCLABLES,
            "PPGM": wt.RECYCLABLES,
            "Papir/Pap/Glas": wt.RECYCLABLES,
            "Papir/Pap og tekstil": wt.RECYCLABLES,
            "Papir/Pap-Metal/Glas": wt.RECYCLABLES,
            "Papir/Pap og Plast/Mad- og drikkekartoner": wt.RECYCLABLES,
            "Papir/småt pap og glas/metal": wt.RECYCLABLES,
            "Pap/papir og glas/metal": wt.RECYCLABLES,
            "Plast/Drikkekarton": wt.RECYCLABLES,
            "Plast/Drikkekarton/Metal": wt.RECYCLABLES,
            "Plast/fødevarekarton": wt.RECYCLABLES,
            "Plast + Mad-/Drikkekartoner": wt.RECYCLABLES,
            "Plast/mad- og drikkekartoner og glas/metal": wt.RECYCLABLES,
            "Metal/Glas/Plast/MDK": wt.RECYCLABLES,
            "Genbrug": wt.RECYCLABLES,
            "Genanvendeligt": wt.RECYCLABLES,
            # Everything else
            "Storskrald": wt.BULKY_WASTE,
            "Miljøkasse": wt.HAZARDOUS,
            "Røde kasser": wt.HAZARDOUS,
            "Tekstilaffald": wt.TEXTILES,
            # Colour only (Nyborg): contents not verifiable
            "Blå": wt.OTHER,
        },
    )
