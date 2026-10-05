import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://servicesgh.renoweb.dk/v1_13"

# Public application key used by RenoWeb's own "Mit Affald" app. This grants the
# same anonymous, read-only access the app itself uses; it is not a per-user
# credential and does not require a MitID login. Identified via briis/affalddk
# (MIT-licensed, https://github.com/briis/affalddk), which uses the same key.
API_KEY = "479D40F4-B3E1-4038-9130-76453188C74C"

# RenoWeb's old "Legacy/JService.asmx" API (used by this source until mid-2025)
# now requires a MitID login and can no longer be used
# (see https://github.com/mampfes/hacs_waste_collection_schedule/issues/4084).
# A number of municipalities that used to run on RenoWeb have also since moved
# their backend entirely to a different vendor (mostly "Perfect Waste"), which
# is not supported by this source.
#
# MUNICIPALITY_CODES only lists the municipalities that are (as of September
# 2026) still served by RenoWeb's public "servicesgh" API, keyed by the
# official Danish municipality ("kommune") code.
MUNICIPALITY_CODES = {
    "aabenraa": "0580",
    "aalborg": "0851",
    "billund": "0530",
    "bornholm": "0400",
    "brondby": "0153",
    "bronderslev": "0810",
    "dragoer": "0155",
    "egedal": "0240",
    "esbjerg": "0561",
    "fredensborg": "0210",
    "gentofte": "0157",
    "glostrup": "0161",
    "hjorring": "0860",
    "jammerbugt": "0849",
    "kerteminde": "0440",
    "mariagerfjord": "0846",
    "randers": "0730",
    "rodovre": "0175",
    "samsoe": "0741",
    "svendborg": "0479",
    "sonderborg": "0540",
    "varde": "0573",
    "vordingborg": "0390",
}

ADDRESS_PATTERN = re.compile(
    r"^\s*(?P<street>.+?)\s+(?P<house_number>\d+)\s*(?P<letter>[A-Za-z]?)"
    r"\s*(?:,\s*(?P<zipcode>\d{4})\b.*)?\s*$"
)

DANISH_TRANSLITERATION = str.maketrans({"æ": "ae", "ø": "o", "å": "aa"})


def _municipality_code(municipality: str) -> str:
    key = municipality.strip().lower().translate(DANISH_TRANSLITERATION)
    if key not in MUNICIPALITY_CODES:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", municipality, sorted(MUNICIPALITY_CODES)
        )
    return MUNICIPALITY_CODES[key]


def _parse_address(address: str) -> re.Match:
    match = ADDRESS_PATTERN.match(address)
    if not match:
        raise SourceArgumentException(
            "address",
            f"Could not parse address '{address}', "
            "expected e.g. 'Torvegade 3, 6700 Esbjerg' or 'Torvegade 3'",
        )
    return match


def _road_id(response, municipality: str, address: str, **_: Any) -> int:
    match = _parse_address(address)
    street = match.group("street").strip()
    zipcode = match.group("zipcode")

    roads = response.json().get("list") or []
    if zipcode:
        roads = [r for r in roads if f"({zipcode})" in r.get("name", "")]

    if not roads:
        raise SourceArgumentNotFoundWithSuggestions("address", street, [])
    if len(roads) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address", street, [r["name"] for r in roads]
        )
    return roads[0]["id"]


def _address_id(response, road_id: int, municipality: str, address: str, **_: Any):
    match = _parse_address(address)
    letter = (match.group("letter") or "").strip()
    label = f"{match.group('street').strip()} {match.group('house_number')}{letter}"

    addresses = response.json().get("list") or []

    # Prefer the main entrance (no floor/suite) matching the given letter
    # (or no letter at all), so a plain "<street> <number>" address doesn't
    # become ambiguous just because the building also has flats.
    main_addresses = [
        a
        for a in addresses
        if not a.get("floor")
        and not a.get("suite")
        and str(a.get("letter", "")).lower() == letter.lower()
    ]
    if main_addresses:
        addresses = main_addresses

    if not addresses:
        raise SourceArgumentNotFoundWithSuggestions("address", label, [])
    if len(addresses) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address", label, [a["presentationString"] for a in addresses]
        )
    return addresses[0]["id"]


def _fraction(record: dict) -> str:
    return str(record.get("module", {}).get("fractionname") or record["name"])


@final
class Source(BaseSource):
    TITLE = "RenoWeb"
    DESCRIPTION = "RenoWeb collections"
    URL = "https://renoweb.dk"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Esbjerg": {
            "municipality": "Esbjerg",
            "address": "Torvegade 3, 6700 Esbjerg",
        },
        "Aalborg": {
            "municipality": "Aalborg",
            "address": "Hasserisvej 97",
        },
        "Rødovre": {
            "municipality": "Rødovre",
            "address": "Rødovre Parkvej 150",
        },
    }

    PARAMS = (
        municipality("municipality"),
        street_address("address"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use the name of your municipality as `municipality` (e.g. "
            "`Esbjerg`, `Aalborg`, `Rødovre`) and your address as `address`, "
            "e.g. `Torvegade 3, 6700 Esbjerg` or just `Torvegade 3`. Only "
            "municipalities served by RenoWeb's public API are supported: "
            + ", ".join(sorted(MUNICIPALITY_CODES))
            + "."
        ),
        "da": (
            "Brug navnet paa din kommune som `municipality` (f.eks. `Esbjerg`, "
            "`Aalborg`, `Rødovre`) og din adresse som `address`, f.eks. "
            "`Torvegade 3, 6700 Esbjerg` eller blot `Torvegade 3`."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.TEXTILES,
        wt.ELECTRONICS,
        wt.OTHER,
    ]

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{API_URL}/GetJSONRoad.aspx",
                params=lambda municipality, address, **_: {
                    "roadname": _parse_address(address).group("street").strip(),
                    "municipalitycode": _municipality_code(municipality),
                    "apikey": API_KEY,
                },
                pick=_road_id,
            ),
            Lookup(
                f"{API_URL}/GetJSONAdress.aspx",
                params=lambda road_id, municipality, address, **_: {
                    "roadid": road_id,
                    "streetBuildingIdentifier": _parse_address(address).group(
                        "house_number"
                    ),
                    "municipalitycode": _municipality_code(municipality),
                    "apikey": API_KEY,
                },
                pick=_address_id,
            ),
        ),
        url=f"{API_URL}/GetJSONContainerList.aspx",
        params=lambda road_id, address_id, municipality, **_: {
            "adressId": address_id,
            "fullinfo": 1,
            "supportsSharedEquipment": 0,
            "municipalitycode": _municipality_code(municipality),
            "apikey": API_KEY,
        },
        raise_for_status=True,
    )
    parse = JsonParser("list")
    # Containers without a regular collection (order-only services) carry an
    # empty timestamp; the transformer skips records without a date.
    transform = JsonTransformer(
        date_key="nextpickupdatetimestamp",
        type_key=_fraction,
        parse_date=date_parsers.from_epoch(),
        carry_raw_label=True,
        type_value_map={
            # Residual / combined residual + food rounds
            "Rest": wt.GENERAL_WASTE,
            "Restaffald": wt.GENERAL_WASTE,
            "Dagrenovation": wt.GENERAL_WASTE,
            "Industri Restaffald": wt.GENERAL_WASTE,
            "Småt brændbart": wt.GENERAL_WASTE,
            "Rest/Mad": wt.GENERAL_WASTE,
            "Rest/madaffald": wt.GENERAL_WASTE,
            "Rest-/madaffald": wt.GENERAL_WASTE,
            "Rest-/Madaffald": wt.GENERAL_WASTE,
            "Rest- og madaffald": wt.GENERAL_WASTE,
            "Mad- og restaffald": wt.GENERAL_WASTE,
            "Mad-/ og restaffald": wt.GENERAL_WASTE,
            "Mad/Rest": wt.GENERAL_WASTE,
            "Mad_Rest": wt.GENERAL_WASTE,
            "Energibeholder (mad/rest)": wt.GENERAL_WASTE,
            "Rest + plast/MDK": wt.GENERAL_WASTE,
            # Food and garden
            "Madaffald": wt.FOOD_WASTE,
            "Haveaffald": wt.GARDEN_WASTE,
            "Frivillig Haveaffald": wt.GARDEN_WASTE,
            "Juletræ": wt.GARDEN_WASTE,
            "Juletræer": wt.GARDEN_WASTE,
            # Paper and glass
            "Papir": wt.PAPER,
            "Pap": wt.PAPER,
            "Papir, pap": wt.PAPER,
            "Papir/Pap": wt.PAPER,
            "Pap/Papir": wt.PAPER,
            "Papir/pap": wt.PAPER,
            "Industri Papir/pap": wt.PAPER,
            "Glas": wt.GLASS,
            "Glas/Metal": wt.GLASS,
            "Metal/glas": wt.GLASS,
            "Metal, glas": wt.GLASS,
            # Combined and mixed recyclables
            "Genbrug": wt.RECYCLABLES,
            "Genanvendeligt": wt.RECYCLABLES,
            "Genbrugsbeholder": wt.RECYCLABLES,
            "Genbrugsspand": wt.RECYCLABLES,
            "Genbrug - PMDK/MG": wt.RECYCLABLES,
            "Genbrug PP": wt.RECYCLABLES,
            "Ressourcebeholder (pap/papir og glas/metal)": wt.RECYCLABLES,
            "Metal": wt.RECYCLABLES,
            "Jern": wt.RECYCLABLES,
            "Plast": wt.RECYCLABLES,
            "Plast-Metal": wt.RECYCLABLES,
            "Plast/ Metal": wt.RECYCLABLES,
            "Plast/metal": wt.RECYCLABLES,
            "Industri Plast/metal": wt.RECYCLABLES,
            "Plast, MDK": wt.RECYCLABLES,
            "Plast+MDK": wt.RECYCLABLES,
            "Plast+MDK/Papir": wt.RECYCLABLES,
            "Plast, MDK/ metal, glas": wt.RECYCLABLES,
            "Plast & mad- og drikkekartoner": wt.RECYCLABLES,
            "Plast/Drikkekarton": wt.RECYCLABLES,
            "Plast/MDK/Metal": wt.RECYCLABLES,
            "Plast/Mad-&Drikkekartoner": wt.RECYCLABLES,
            "Plast/Mad-&Drikkekartoner/Papir/Pap": wt.RECYCLABLES,
            "Plast/Metal/Mad- & drikkekartoner": wt.RECYCLABLES,
            "Plast/Papir": wt.RECYCLABLES,
            "Plast_Metal_Papir": wt.RECYCLABLES,
            "Papir/Plast og kartoner": wt.RECYCLABLES,
            "Papir/pap + glas/metal": wt.RECYCLABLES,
            "Papir og pap/Glas": wt.RECYCLABLES,
            "Glas-Papir": wt.RECYCLABLES,
            # Bulky, hazardous, textiles, electronics
            "Storskrald": wt.BULKY_WASTE,
            "Storskrald - Kræver tilmelding": wt.BULKY_WASTE,
            "Miljøkasse": wt.HAZARDOUS,
            "Miljøboks": wt.HAZARDOUS,
            "Farligt affald": wt.HAZARDOUS,
            "Industri Batterier": wt.HAZARDOUS,
            "Tekstilaffald": wt.TEXTILES,
            "Småt elektronik": wt.ELECTRONICS,
            "Industri Småt elektronik": wt.ELECTRONICS,
            # Local names whose contents cannot be verified
            "Energispand": wt.OTHER,
            "Genbrugsbilen": wt.OTHER,
            "Nedgravede": wt.OTHER,
            "Beholderværksted": wt.OTHER,
            "Porcelæn": wt.OTHER,
            "Industri Flasker": wt.OTHER,
        },
    )
