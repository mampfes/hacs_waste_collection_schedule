from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import EachResponse, JsonParser
from waste_collection_schedule.preprocessors import Deduplicate
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

_CONTROLLER_URL = "https://uod.kostak.si/Controller.php"


def _label(entry: dict) -> str:
    return f"{entry['street_name']} {entry['location_hn']}{entry['location_hna']}"


def _normalize(value: str) -> str:
    return "".join(value.casefold().split())


def _schedule_codes(response, *keys, address, **_) -> list[str]:
    """The schedule codes (mixed waste, packaging, bio) of the address."""
    entries = response.json()
    wanted = _normalize(address)
    match = next((e for e in entries if _normalize(_label(e)) == wanted), None)
    if match is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, sorted({_label(e) for e in entries})
        )
    return [
        code.strip()
        for code in (match["dan_MKO"], match["dan_EMB"], match["dan_BIO"])
        if code and code.strip()
    ]


@final
class Source(BaseSource):
    TITLE = "Kostak Krško"
    DESCRIPTION = "Source for Kostak d.o.o. waste collection in Krško, Slovenia."
    URL = "https://www.kostak.si"
    COUNTRY = "si"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Senuše 3": {"address": "Senuše 3"},
        "Cesta krških žrtev 134A": {"address": "Cesta krških žrtev 134A"},
        "Titova cesta 1": {"address": "Titova cesta 1"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your address at https://uod.kostak.si/ and enter it "
            "as street name, house number and optional house number suffix, "
            "for example 'Senuše 3' or 'Cesta krških žrtev 134A'."
        ),
        "sl": (
            "Naslov poiščite na https://uod.kostak.si/ in ga vnesite kot ulica, "
            "hišna številka in morebitna dodatna oznaka, na primer 'Senuše 3' "
            "ali 'Cesta krških žrtev 134A'."
        ),
    }

    PARAMS = (street_address(),)

    # One schedule code per waste stream (an address may lack packaging or bio);
    # each code is fetched on its own.
    retrieve = FanOutRetriever(
        prepare=Lookup(
            _CONTROLLER_URL,
            params=lambda address, **_: {"find": address},
            pick=_schedule_codes,
        ),
        targets=lambda source, codes: codes,
        fetch=Request(
            _CONTROLLER_URL,
            params=lambda code, codes, **_: {"getDates": code},
        ),
    )
    parse = EachResponse(JsonParser())
    preprocess = Deduplicate(key=lambda item: (item["DT"], item["odvoz"]))
    transform = JsonTransformer(
        date_key="DT",
        type_key=lambda item: item["odvoz"].split()[0],
        type_value_map={
            "MKO": wt.GENERAL_WASTE,
            "EMB": wt.RECYCLABLES,
            "BIO": wt.ORGANIC,
        },
    )
