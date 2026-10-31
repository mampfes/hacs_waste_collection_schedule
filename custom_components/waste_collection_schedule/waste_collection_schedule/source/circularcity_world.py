"""Circular City (circularcity.world), France.

Circular City runs white-label waste apps for French local authorities (Lunel
Agglo's https://dechets.lunelagglo.fr, Syndicat Émeraude's app, ...). Every
deployment talks to the same public API, keyed by the customer's slug and
numeric id (both are printed in the deployment's page data):

1. ``POST https://addresses.circularcity.world/addresses/search-city`` with the
   customer slug and the typed address returns matching addresses, each with
   its BAN-style id ("34296_0040_00041").
2. ``GET https://api.circularcity.world/exutoires/collection-address/collection``
   with that id, the customer id and a date window returns one entry per waste
   stream (``HOUSEHOLD_WASTE``, ``SELECTIVE_SORTING``, ``PAPER``, ``GLASS``,
   ...), each with its list of collection instants, or ``null`` for a stream
   the address does not have.

The instants are UTC ("2026-10-26T16:00:00.000Z" is an evening round), so they
are read in Europe/Paris. Other Circular City customers (Paris Terres d'Envol,
Lisieux Normandie) use the platform for sorting guides only and answer every
address with 404, so they are not listed; Montpellier and Maubeuge sit behind
a password.
"""

import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import Compose, ExplodeList, FlattenGroups
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

ADDRESS_URL = "https://addresses.circularcity.world/addresses/search-city"
COLLECTION_URL = (
    "https://api.circularcity.world/exutoires/collection-address/collection"
)

# Customer slug -> (customer id, display name, public site). Needed while
# fetching, so it stays in Python.
_CUSTOMERS = {
    "lunel": ("8", "Lunel Agglo", "https://dechets.lunelagglo.fr"),
    "emeraude": ("41", "Syndicat Émeraude", "https://emeraude.circularcity.world"),
}

_DAYS_AHEAD = 365


def _address_query(customer: str, address: str, **_: Any) -> dict:
    return {
        "data": {
            "type": "search",
            "attributes": {"search": address, "city": customer},
        }
    }


def _address_id(response: Any, *_keys: Any, address: str, **_: Any) -> str:
    """The id of the search result spelled like the configured address."""
    results = [item.get("attributes") or {} for item in response.json()["data"]]
    wanted = lookups.normalize_loose(address)
    for result in results:
        if lookups.normalize_loose(result.get("adresse_complete", "")) == wanted:
            return result["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address",
        address,
        [r["adresse_complete"] for r in results[:10] if r.get("adresse_complete")],
    )


def _window(address_id: str, customer: str, **_: Any) -> dict:
    today = datetime.date.today()
    return {
        "addressId": address_id,
        "customerId": _CUSTOMERS[customer][0],
        "startYearMonthDay": today.isoformat(),
        "endYearMonthDay": (today + datetime.timedelta(days=_DAYS_AHEAD)).isoformat(),
        "useFlux": "true",
    }


@final
class Source(BaseSource):
    TITLE = "Circular City"
    DESCRIPTION = "Source for local authorities using the Circular City waste app."
    URL = "https://circularcity.world"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Lunel Agglo, Boisseron": {
            "customer": "lunel",
            "address": "50 Rue des Hauts de Boisseron 34160 Boisseron",
        },
        "Syndicat Émeraude, Montlignon": {
            "customer": "emeraude",
            "address": "94 Rue de Paris 95680 Montlignon",
        },
    }

    PARAMS = (
        dropdown("customer", list(_CUSTOMERS), label="Customer"),
        street_address(),
    )

    REGIONS: ClassVar[list] = [
        region(name, url=site, customer=slug)
        for slug, (_, name, site) in _CUSTOMERS.items()
    ]

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.BULKY_WASTE,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick your authority's Circular City app as the customer and enter "
            "your address exactly as the app's address search suggests it, "
            "including postcode and town (e.g. '41 Place de la Mairie 34160 "
            "Saussines')."
        ),
        "fr": (
            "Choisissez l'application Circular City de votre collectivité et "
            "saisissez votre adresse telle que la recherche d'adresse de "
            "l'application la propose, avec code postal et commune (par ex. "
            "« 41 Place de la Mairie 34160 Saussines »)."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                ADDRESS_URL, method="POST", json=_address_query, pick=_address_id
            ),
        ),
        url=COLLECTION_URL,
        params=_window,
    )
    parse = parsers.JsonParser("data", "attributes")
    preprocess = Compose(FlattenGroups(), ExplodeList("dates", into="date"))
    transform = JsonTransformer(
        date_key="date",
        type_key="name",
        parse_date=date_parsers.in_timezone("Europe/Paris"),
        type_value_map={
            "HOUSEHOLD_WASTE": wt.GENERAL_WASTE,
            "SELECTIVE_SORTING": wt.RECYCLABLES,
            "PAPER": wt.PAPER,
            "GLASS": wt.GLASS,
            "GREEN_WASTE": wt.GARDEN_WASTE,
            "COMPOSTING": wt.ORGANIC,
            "BULKY_WASTE": wt.BULKY_WASTE,
            "MOBILE_BULKY_WASTE": wt.BULKY_WASTE,
            "TOXIC_WASTE": wt.HAZARDOUS,
        },
    )
