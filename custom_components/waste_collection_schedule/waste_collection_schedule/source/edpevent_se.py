from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.EdpFutureWeb import (
    TYPE_VALUE_MAP,
    EdpFutureWebParser,
    EdpFutureWebRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

# The deployments of the EDP Future module this source knows by name. Read at
# fetch time (the api_url), so it stays in Python; update_docu_links.py lists
# the keys in doc/source/edpevent_se.md.
SERVICE_PROVIDERS = {
    "skelleftea": {
        "title": "Skellefteå",
        "url": "https://skelleftea.se",
        "api_url": "https://wwwtk2.skelleftea.se/FutureWeb/SimpleWastePickup",
    },
    "boden": {
        "title": "Boden",
        "url": "https://boden.se",
        "api_url": "https://edpmobile.boden.se/FutureWeb/SimpleWastePickup",
    },
    "ssam": {
        "title": "SSAM Södra Smalånds Avfall & Miljö",
        "url": "https://ssam.se",
        "api_url": "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup",
    },
    "uppsalavatten": {
        "title": "Uppsala Vatten",
        "url": "https://uppsalavatten.se",
        "api_url": "https://futureweb.uppsalavatten.se/Uppsala/FutureWeb/SimpleWastePickup",
    },
    "boras": {
        "title": "Borås Energi och Miljö",
        "url": "https://www.borasem.se",
        "api_url": "https://kundportal.borasem.se/EDPFutureWeb/SimpleWastePickup",
    },
    "roslagsvatten": {
        "title": "Roslagsvatten",
        "url": "https://roslagsvatten.se",
        "api_url": "https://edpmypage.roslagsvatten.se/FutureWebOS/SimpleWastePickup",
    },
    "kretslopp-sydost": {
        "title": "Kretslopp Sydost",
        "url": "https://kretsloppsydost.se",
        "api_url": "https://kundportal.kretsloppsydost.se/FutureWeb/SimpleWastePickup",
    },
    "marks-kommun": {
        "title": "Marks kommun",
        "url": "https://www.mark.se",
        "api_url": "https://va-renhallning.mark.se/FutureWeb/SimpleWastePickup",
    },
    "lycksele-kommun": {
        "title": "Lycksele Kommun",
        "url": "https://www.lycksele.se",
        "api_url": "https://future.lycksele.se/FutureWeb/SimpleWastePickup",
    },
    "kiruna-kommun": {
        "title": "Kiruna - Tekniska Verken",
        "url": "https://www.tekniskaverkenikiruna.se",
        "api_url": "https://kund.tekniskaverkenikiruna.se/FutureWebBasic/SimpleWastePickup",
    },
    "lidkopings-kommun": {
        "title": "Lidköpings kommun",
        "url": "https://lidkoping.se",
        "api_url": "https://futureweb.lidkoping.se/FutureWebBasic/SimpleWastePickup",
    },
    "stenungsund-kommun": {
        "title": "Stenungsunds kommun",
        "url": "https://www.stenungsund.se/",
        "api_url": "https://futureweb.stenungsund.se/FutureWebBasic/SimpleWastePickup",
    },
    "orust-kommun": {
        "title": "Orust kommun",
        "url": "https://orust.se/",
        "api_url": "https://va-renhallning-minasidor.orust.se/FutureWebBasic/SimpleWastePickup",
    },
    "ljungby-kommun": {
        "title": "Ljungby kommun",
        "url": "https://ljungby.se/",
        "api_url": "https://edpwebb.ljungby.se/FutureWeb/SimpleWastePickup",
    },
    "orebro-kommun": {
        "title": "Örebro kommun",
        "url": "https://www.orebro.se",
        "api_url": "https://futureweb.orebro.se/FutureWeb/SimpleWastePickup",
    },
    "herrljunga-vargarda": {
        "title": "Herrljunga & Vårgårda kommun",
        "url": "https://www.remondisrecycling.se/hushallsavfall/herrljunga-vargarda/",
        "api_url": "https://edpfuture.remondis.se/EDPFutureWeb/SimpleWastePickup",
    },
    "vafabmiljo": {
        "title": "Vafab Miljö",
        "url": "https://vafabmiljo.se",
        "api_url": "https://services.vafabmiljo.se/FutureWebVKFHus/SimpleWastePickup",
    },
    "nvoa": {
        "title": "NVOA - Nacka Vatten och Avfall",
        "url": "https://www.nacka.se/nackavattenavfall/avfall/sophamtning/tomningsdag/",
        "api_url": "https://futureweb.nvoa.se/EDP/FutureWebBasic/SimpleWastePickup",
    },
    "danderyd": {
        "title": "Danderyds kommun",
        "url": "https://www.danderyd.se",
        "api_url": "https://future.danderyd.se/Danderyd/EDPFutureweb/SimpleWastePickup",
    },
}


def _api_url(service_provider=None, url=None, **_) -> str:
    """The deployment to ask: the ``url`` given, else the named provider's."""
    if url:
        return url
    if not service_provider:
        raise SourceArgumentExceptionMultiple(
            ["service_provider", "url"],
            "You must provide either a service provider or a url",
        )
    provider = SERVICE_PROVIDERS.get(service_provider.lower())
    if provider is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "service_provider", service_provider, SERVICE_PROVIDERS.keys()
        )
    return provider["api_url"]


@final
class Source(BaseSource):
    TITLE = "EDPEvent - Multi Source"
    DESCRIPTION = (
        "Source for all EDPEvent waste collection sources. This included multiple "
        "municipalities in Sweden."
    )
    URL = "https://www.edpevent.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.HAZARDOUS,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    REGIONS = tuple(
        region(data["title"], url=data["url"], service_provider=provider)
        for provider, data in SERVICE_PROVIDERS.items()
    )

    TEST_CASES: ClassVar[dict] = {
        "https://edpmypage.roslagsvatten.se/FutureWebOS/SimpleWastePickup, Andromedavägen 1, Åkersberga": {
            "street_address": "Andromedavägen 1",
            "url": "https://edpmypage.roslagsvatten.se/FutureWebOS/SimpleWastePickup",
        },
        "Boden - Bodens Kommun": {
            "street_address": "KYRKGATAN 24",
            "service_provider": "boden",
        },
        "Boden - Gymnasiet": {
            "street_address": "IDROTTSGATAN 4",
            "url": "https://edpmobile.boden.se/FutureWeb/SimpleWastePickup",
        },
        "Uppsalavatten - Test1": {
            "street_address": "SADELVÄGEN 1",
            "url": "https://futureweb.uppsalavatten.se/Uppsala/FutureWeb/SimpleWastePickup",
        },
        "Uppsalavatten - Test2": {
            "street_address": "BJÖRKLINGE-GRÄNBY 33",
            "service_provider": "uppsalavatten",
        },
        "Uppsalavatten - Test3": {
            "street_address": "BJÖRKLINGE-GRÄNBY 20",
            "service_provider": "uppsalavatten",
        },
        "SSAM - Home": {
            "street_address": "Asteroidvägen 1, Växjö",
            "service_provider": "ssam",
        },
        "SSAM - Slambrunn": {
            "street_address": "Svanebro Ormesberga, Ör",
            "service_provider": "ssam",
        },
        "Skelleftea - Test1": {
            "street_address": "Frögatan 76 -150",
            "service_provider": "skelleftea",
        },
        "Borås - Test1": {
            "street_address": "Länghemsgatan 10",
            "service_provider": "boras",
        },
        "Borås - Test2": {
            "street_address": "Yttre Näs 1, Borås",
            "service_provider": "boras",
        },
        "Borås - Test3": {
            "street_address": "Stora Hyberg 1, Brämhult",
            "url": "https://kundportal.borasem.se/EDPFutureWeb/SimpleWastePickup",
        },
        "Kretslopp Sydost Hägnevägen 1, Sävsjö": {
            "street_address": "Hägnevägen 1, Sävsjö",
            "service_provider": "kretslopp-sydost",
        },
        "marks-kommun": {
            "street_address": "Habyvägen 13, skene",
            "service_provider": "marks-kommun",
        },
        "Lycksele": {
            "street_address": "STORGATAN   efter nr 103, LYCKSELE",
            "service_provider": "lycksele-kommun",
        },
        "Kiruna - Tekniska Verken": {
            "street_address": "Värmeverksvägen 12, Kiruna",
            "service_provider": "kiruna-kommun",
        },
        "Lidköping - Stadshuset": {
            "street_address": "SKARAGATAN 8 -12, STADSHUSET",
            "service_provider": "lidkopings-kommun",
        },
        "Stenungsund - Kommunhuset": {
            "street_address": "Strandvägen 15, Stenungsund",
            "service_provider": "stenungsund-kommun",
        },
        "Orust - Kommunhuset": {
            "street_address": "ÅVÄGEN 2 -6, Henån",
            "service_provider": "orust-kommun",
        },
        "Ljungby kommun - kommunhuset": {
            "street_address": "Olofsgatan 9 / Kommunhuset, Ljungby",
            "service_provider": "ljungby-kommun",
        },
        "Örebro - Kommunstyrelsen": {
            "street_address": "Ringgatan 32",
            "service_provider": "orebro-kommun",
        },
        "Herrljunga": {
            "street_address": "Storgatan 5, Herrljunga",
            "url": "https://edpfuture.remondis.se/EDPFutureWeb/SimpleWastePickup",
        },
        "Vårgårda": {
            "street_address": "Vårgårda Herrgård, VÅRGÅRDA",
            "url": "https://edpfuture.remondis.se/EDPFutureWeb/SimpleWastePickup",
        },
        "Vafab Miljö - Test": {
            "street_address": "Gasverksgatan 7, Västerås",
            "service_provider": "vafabmiljo",
        },
        "NVOA - Nacka (Fogdevägen)": {
            "street_address": "Fogdevägen 13, Saltsjö-Duvnäs",
            "service_provider": "nvoa",
        },
        "Danderyd - Banérvägen 6": {
            "street_address": "Banérvägen 6",
            "service_provider": "danderyd",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {
            "street_address": "Ingen gata 999",
            "service_provider": "ssam",
        },
        "Unknown provider": {
            "street_address": "Asteroidvägen 1, Växjö",
            "service_provider": "nowhere",
        },
    }

    PARAMS = (
        street_address("street_address"),
        text_field("service_provider", "Service provider", optional=True),
        text_field("url", "URL", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as the provider's own search lists it, "
            "and either the service provider key (see the list below) or the "
            "URL of your provider's EDP Future page ending in "
            "'/SimpleWastePickup'."
        ),
    }

    retrieve = EdpFutureWebRetriever(_api_url)
    parse = EdpFutureWebParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        carry_raw_label=True,
    )
