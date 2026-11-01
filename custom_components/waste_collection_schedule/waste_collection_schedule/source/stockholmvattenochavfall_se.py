"""House and townhouse collections from Stockholm Vatten och Avfall."""

import re
from typing import ClassVar, TypedDict, final

from waste_collection_schedule import date_parsers, field_terms, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://www.stockholmvattenochavfall.se/villa-och-radhus/avfallstjanster/nar-kommer-sopbilen"
AUTOCOMPLETE_URL = f"{API_URL}/AutoCompleteMe"


# The autocomplete answers at most this many addresses per query.
_AUTOCOMPLETE_LIMIT = 5
# Bound dropdown discovery on long streets; users can still type an address.
_MAX_QUERIES = 60
_STREET_OF = re.compile(r"^(.*?)\s+\d+\w*,")

_AUTOCOMPLETE = retrievers.Request(
    AUTOCOMPLETE_URL,
    params=lambda query, *args, **kwargs: {"query": query},
)


class _Collection(TypedDict):
    group: str
    executionDate: str


def _normalise(value: str) -> str:
    return " ".join(value.casefold().replace(",", " ").split())


def _address(response, *keys, address=None, street=None, **params) -> str:
    """The full address ("Street 1, District, 123 45") the address search matched.

    The search page only accepts the complete address, so a partial one is
    completed through the same autocomplete the website uses.
    """
    address = address or street or ""
    values = [str(r["value"]) for r in response.json() or [] if r.get("value")]
    if not values:
        raise SourceArgumentNotFound("address", address)
    wanted = _normalise(address)
    exact = [v for v in values if _normalise(v) == wanted]
    if len(exact) == 1:
        return exact[0]
    # "Street 1, District" without the postcode, or without the district.
    partial = [v for v in values if _normalise(v).startswith(wanted + " ")]
    if len(partial) == 1:
        return partial[0]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, values if not partial else partial
    )


@final
class Source(BaseSource):
    TITLE = "Stockholm Vatten och Avfall"
    DESCRIPTION = (
        "Source for Stockholm Vatten och Avfall (SVOA), "
        "house and townhouse waste collection in Stockholm."
    )
    URL = "https://www.stockholmvattenochavfall.se"
    COUNTRY = "se"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@chaudis"]
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": (
            "In the UI, type the street name and then pick your address from the list. "
            "Enter the address of a house or townhouse (villa och radhus) as on "
            "https://www.stockholmvattenochavfall.se/villa-och-radhus/avfallstjanster/nar-kommer-sopbilen/, "
            "e.g. `Hjortronvägen 3, Bromma`. The postcode is optional. "
            "The website only shows the next collection of each bin, so the "
            "schedule is refreshed once a day (the default fetch interval)."
        ),
        "sv": (
            "I gränssnittet skriver du gatunamnet och väljer sedan din adress i listan. "
            "Ange adressen till en villa eller ett radhus som på "
            "https://www.stockholmvattenochavfall.se/villa-och-radhus/avfallstjanster/nar-kommer-sopbilen/, "
            "t.ex. `Hjortronvägen 3, Bromma`. Postnumret är valfritt. "
            "Webbplatsen visar bara nästa tömning av varje kärl, så schemat "
            "uppdateras en gång om dagen (standardintervallet)."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.GLASS,
        wt.METAL,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Hjortronvägen 3, Bromma": {"address": "Hjortronvägen 3, Bromma"},
        "Street and address": {
            "street": "Hjortronvägen",
            "address": "Hjortronvägen 3, Bromma, 168 59",
        },
        "Doktor Abrahams väg 4, Bromma, 168 58": {
            "address": "Doktor Abrahams väg 4, Bromma, 168 58"
        },
        "Stenborgsvägen 4, Hägersten, 129 38": {
            "address": "Stenborgsvägen 4, Hägersten, 129 38"
        },
        "Björkvägen 3, Enskede": {"address": "Björkvägen 3, Enskede"},
        "Gamla Tyresövägen 305, Enskededalen": {
            "address": "Gamla Tyresövägen 305, Enskededalen"
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "Ingen gata 999, Stockholm"},
        "Uncovered apartment address": {"address": "Drottninggatan 1"},
    }

    def _raise_empty(self) -> None:
        raise SourceArgumentNotFound(
            "address",
            self.params.get("address") or self.params.get("street"),
            "only house and townhouse (villa och radhus) addresses are covered.",
        )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[str]:
        """The addresses on the chosen street, for the config flow's dropdown.

        The street is free text. The autocomplete only returns five addresses
        per query, so the street's house numbers are walked by number prefix.
        """
        street = str(selections.get("street") or "").strip()
        if field != "address" or not street:
            return []
        walker = retrievers.detached_source()
        queries = 0

        def search(query: str) -> list[str]:
            nonlocal queries
            queries += 1
            reply = _AUTOCOMPLETE(walker, query).json() or []
            return [str(r["value"]) for r in reply if r.get("value")]

        found: dict[str, None] = dict.fromkeys(search(street))
        streets = {m.group(1) for a in found if (m := _STREET_OF.match(a))}
        for name in sorted(streets)[:_AUTOCOMPLETE_LIMIT]:
            pending = [f"{name} {digit}" for digit in "123456789"]
            while pending and queries < _MAX_QUERIES:
                query = pending.pop(0)
                results = search(query)
                found.update(dict.fromkeys(results))
                if len(results) >= _AUTOCOMPLETE_LIMIT:
                    pending += [query + digit for digit in "0123456789"]
        return sorted(
            found,
            key=lambda a: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", a)],
        )

    PARAMS = (
        cascading_select(
            ("street", field_terms.STREET),
            ("address", field_terms.ADDRESS),
        ),
    )

    retrieve = retrievers.Request(
        f"{API_URL}/Search",
        params=lambda full_address, **kwargs: {"address": full_address},
        before=(
            retrievers.Lookup(
                AUTOCOMPLETE_URL,
                params=lambda address=None, street=None, **kwargs: {
                    "query": address or street
                },
                pick=_address,
            ),
        ),
    )
    parse = JsonParser(shape=list[_Collection])

    transform = JsonTransformer(
        date_key="executionDate",
        type_key="group",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Kärl 1 - restavfall och matavfall": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
            "Kärl 2 - papper och plast": [wt.PAPER, wt.PLASTIC],
            "Kärl 3 - glas och metall": [wt.GLASS, wt.METAL],
            "Trädgårdsavfall, villa": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
