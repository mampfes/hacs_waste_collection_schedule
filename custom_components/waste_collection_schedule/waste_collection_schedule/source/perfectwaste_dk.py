import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    ExplodeList,
    RequireRecords,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

# Firebase callable functions behind the Perfect Waste app (dk.perfectwaste.app
# and the municipality-branded variants). Both are read-only and anonymous; the
# app's write call that registers a new address (fetchAddressAndSaveToDb) is
# deliberately never used, see HOWTO.
_API = "https://europe-west3-perfect-waste.cloudfunctions.net"

# Municipality name -> official Danish municipality ("kommune") code. Only the
# municipalities whose Perfect Waste integration answered both the address
# search and the collection lookup for at least one address (October 2026).
# Lyngby-Taarbæk and Rødovre have an integration but returned no collection
# dates for any tested address, so they are left out.
_MUNICIPALITIES = {
    "Albertslund": 165,
    "Allerød": 201,
    "Ballerup": 151,
    "Faxe": 320,
    "Frederiksberg": 147,
    "Frederikssund": 250,
    "Gladsaxe": 159,
    "Greve": 253,
    "Gribskov": 270,
    "Guldborgsund": 376,
    "Halsnæs": 260,
    "Helsingør": 217,
    "Hillerød": 219,
    "Horsens": 615,
    "Hvidovre": 167,
    "Høje-Taastrup": 169,
    "Hørsholm": 223,
    "Kalundborg": 326,
    "Køge": 259,
    "Lejre": 350,
    "Lolland": 360,
    "Næstved": 370,
    "Odsherred": 306,
    "Ringkøbing-Skjern": 760,
    "Roskilde": 265,
    "Rudersdal": 230,
    "Slagelse": 330,
    "Solrød": 269,
    "Stevns": 336,
    "Tårnby": 185,
    "Varde": 573,
    "Vejen": 575,
    "Vordingborg": 390,
}

_NO_DATES_HINT = (
    "the address exists in Perfect Waste, but Perfect Waste has no collection "
    "dates stored for it yet. Add the address once in the Perfect Waste app "
    "(or your municipality's own Perfect Waste app), then reload this source"
)

# Mad- og drikkekartoner (food and drink cartons) contain "mad" but are not
# food waste, so they are matched (and removed) before the other keywords.
_CARTONS = re.compile(
    r"mad-?\s*(?:og|&)?\s*-?\s*drikkekarton\w*|md-?karton\w*|\bmdk\b|drikkekarton\w*"
)

# Keyword -> canonical type, in the order the types are listed for a combined
# fraction ("Rest/Mad" is one bin with two compartments).
_KEYWORDS = (
    (("farligt", "miljøkasse", "miljøboks", "batteri"), "hazardous"),
    (("elektronik",), "electronics"),
    (("storskrald",), "bulky"),
    (("have",), "garden"),
    (("rest", "dagrenovation", "brændbart"), "general"),
    (("mad",), "food"),
    (("pap",), "paper"),  # papir, pap, PAPPI
    (("plast",), "plastic"),
    (("glas",), "glass"),
    (("metal", "dåse"), "metal"),
    (("tekstil",), "textiles"),
)

_TYPE_MAP = {
    "hazardous": wt.HAZARDOUS,
    "electronics": wt.ELECTRONICS,
    "bulky": wt.BULKY_WASTE,
    "garden": wt.GARDEN_WASTE,
    "general": wt.GENERAL_WASTE,
    "food": wt.FOOD_WASTE,
    "paper": wt.PAPER,
    "plastic": wt.PLASTIC,
    "glass": wt.GLASS,
    "metal": wt.METAL,
    "cartons": wt.CARTONS,
    "textiles": wt.TEXTILES,
    "recyclables": wt.RECYCLABLES,
    "other": wt.OTHER,
}


def _fraction_types(name: str) -> list[str]:
    """The canonical type keys a Perfect Waste fraction name stands for.

    Every municipality names its fractions itself ("Rest/Mad", "Papir/Plast &
    MDK", "240 l beh. papir/pap - metal/plast/drikkekarton"), so the materials
    are read from keywords. A combined fraction yields each of its materials;
    a name with no known keyword is passed on verbatim for the shared
    vocabulary to resolve.
    """
    text = name.casefold()
    if "dispenser" in text or "genbrugshal" in text:
        return ["other"]
    keys = []
    if _CARTONS.search(text):
        text = _CARTONS.sub(" ", text)
        keys.append("cartons")
    keys = [
        key
        for words, key in _KEYWORDS
        if any(word in text for word in words) and key not in keys
    ] + keys
    if not keys and ("genbrug" in text or "genanvend" in text):
        keys = ["recyclables"]
    return keys or [name]


def _items(record: dict[str, Any], _source: Any) -> list[dict[str, str]]:
    return [
        {"type": key, "label": fraction["fractionName"]}
        for fraction in record.get("fractions") or []
        if fraction.get("fractionName")
        for key in _fraction_types(fraction["fractionName"])
    ]


def _address_id(response: Any, *, address: str, **_: Any) -> str:
    hits = {
        hit["displayName"]: str(hit["addressID"])
        for hit in response.json().get("result") or []
        if hit.get("displayName") and hit.get("addressID")
    }
    wanted = lookups.normalize_loose(address)
    for name, address_id in hits.items():
        if lookups.normalize_loose(name) == wanted:
            return address_id
    # "Søndermarken 10" for "Søndermarken 10, 8752 Østbirk", if it is unique.
    street_only = [
        address_id
        for name, address_id in hits.items()
        if lookups.normalize_loose(name.split(",")[0]) == wanted
    ]
    if len(street_only) == 1:
        return street_only[0]
    if not hits:
        raise SourceArgumentNotFound(
            "address",
            address,
            "enter the address as the Perfect Waste app shows it, "
            'e.g. "Søndermarken 10, 8752 Østbirk"',
        )
    raise SourceArgumentNotFoundWithSuggestions("address", address, list(hits))


@final
class Source(BaseSource):
    TITLE = "Perfect Waste"
    DESCRIPTION = "Source for Danish municipalities using the Perfect Waste app."
    URL = "https://perfectwaste.dk"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Horsens Ostbirk": {
            "municipality": "Horsens",
            "address": "Søndermarken 10, 8752 Østbirk",
        },
        "Rudersdal Birkerod": {
            "municipality": "Rudersdal",
            "address": "Stationsvej 38, 3460 Birkerød",
        },
        "Koge": {"municipality": "Køge", "address": "Bakkevej 3, 4600 Køge"},
    }

    PARAMS = (
        dropdown("municipality", list(_MUNICIPALITIES), label="Municipality"),
        street_address(),
    )

    REGIONS = tuple(
        region(f"{name} Kommune", municipality=name) for name in _MUNICIPALITIES
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your municipality and enter your address the way the Perfect "
            'Waste app writes it, e.g. "Søndermarken 10, 8752 Østbirk". If the '
            "address is ambiguous, the error message lists the matching "
            "addresses. Important: Perfect Waste only returns collection dates "
            "for addresses it already knows. If you get an error saying there "
            "are no collection dates stored for your address, add the address "
            "once in the Perfect Waste app (or your municipality's own Perfect "
            "Waste app) and then reload this source."
        ),
        "da": (
            "Vælg din kommune og indtast adressen, som Perfect Waste-appen "
            'skriver den, f.eks. "Søndermarken 10, 8752 Østbirk". Hvis adressen '
            "ikke er entydig, viser fejlbeskeden de mulige adresser. Vigtigt: "
            "Perfect Waste returnerer kun tømmedage for adresser, som systemet "
            "allerede kender. Får du en fejl om, at der ikke er gemt tømmedage "
            "for din adresse, så tilføj adressen én gang i Perfect Waste-appen "
            "(eller din kommunes egen Perfect Waste-app) og genindlæs derefter "
            "denne kilde."
        ),
    }

    retrieve = retrievers.Request(
        f"{_API}/getAddressCollections",
        method="POST",
        json=lambda address_id, municipality, **_: {
            "data": {
                "addressID": address_id,
                "municipality": _MUNICIPALITIES[municipality],
            }
        },
        before=[
            retrievers.Lookup(
                f"{_API}/searchExternalAddresses",
                method="POST",
                json=lambda address, municipality, **_: {
                    "data": {
                        "query": address,
                        "municipality": _MUNICIPALITIES[municipality],
                        "page": 1,
                        "onlyManual": False,
                    }
                },
                pick=_address_id,
            )
        ],
        timeout=60,
    )

    parse = parsers.JsonParser("result")

    preprocess = Compose(
        RequireRecords(argument="address", hint=_NO_DATES_HINT),
        ExplodeList(_items, into="item"),
    )

    transform = JsonTransformer(
        date_key=lambda record: str(record.get("date") or "")[:10],
        type_key=lambda record: record["item"]["type"],
        description_key=lambda record: record["item"]["label"],
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        skip_unparseable_dates=True,
        type_value_map=_TYPE_MAP,
    )
