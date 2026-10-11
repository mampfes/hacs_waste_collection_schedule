from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    house_number,
    municipality,
    street,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Sammelkalender import (
    calendar_retriever,
    split_types,
)
from waste_collection_schedule.transformers import JsonTransformer

SERVICES = {
    "zeba": {
        "title": "Zeba",
        "url": "https://www.zebazug.ch",
        "search": "https://www.zeba.sammelkalender.ch/kunden_WANN_auswahl_form.php",
        "collections": "https://www.zeba.sammelkalender.ch/kunden_sammlung_ausw_cont.php",
    },
    "zkri": {
        "title": "ZKRI",
        "url": "https://zkri.ch",
        "search": "https://daten.zkri.ch/web/Sammelkalender/kunden_WANN_auswahl_form.php",
        "collections": "https://daten.zkri.ch/web/Sammelkalender/kunden_sammlung_ausw_cont.php",
    },
    "real_luzern": {
        "title": "Real Luzern",
        "url": "https://www.realluzern.ch",
        "search": "https://www.real.sammelkalender.ch/app/appSelect.php",
        "collections": "https://www.real.sammelkalender.ch/app/appSammeldaten.php",
    },
    "zaku": {
        "title": "ZAKU Entsorgung",
        "url": "https://www.zaku.ch",
        "search": "https://www.zaku.sammelkalender.ch/appSelect.php",
        "collections": "https://www.zaku.sammelkalender.ch/appSammeldaten.php",
    },
}

_TYPE_MAP = {
    "Kehricht": wt.GENERAL_WASTE,
    "Grüngut": wt.GARDEN_WASTE,
    "Karton": wt.PAPER,
    "Papier": wt.PAPER,
    "Alteisen/Metall": wt.METAL,
    "Christbaum": wt.OTHER,
    "Häckseldienst": wt.GARDEN_WASTE,
    "Repair Café": wt.OTHER,
    "Ökihof geschlossen": wt.OTHER,
}


@final
class Source(BaseSource):
    TITLE = "Sammelkalender.ch"
    DESCRIPTION = "Source for Sammelkalender.ch."
    URL = "https://info.sammelkalender.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.METAL,
        wt.OTHER,
    ]

    REGIONS = tuple(
        region(s["title"], url=s["url"], service_provider=key)
        for key, s in SERVICES.items()
    )

    TEST_CASES: ClassVar[dict] = {
        "zeba Baar Aberenrain 10": {
            "service_provider": "zeba",
            "municipality": "Baar",
            "street": "Aberenrain",
            "hnr": 10,
        },
        "zkri Rothenthurm": {
            "service_provider": "zkri",
            "municipality": "Rothenthurm",
        },
        "ZKRI, Schwyz, Alte Gasse (Seewen)": {
            "service_provider": "zkri",
            "municipality": "Schwyz",
            "street": "Alte Gasse (Seewen)",
        },
        "Real Luzern, Meggen": {
            "service_provider": "real_luzern",
            "municipality": "Meggen",
        },
        "Real Luzern, Malters, Bachweg": {
            "service_provider": "real_luzern",
            "municipality": "Malters",
            "street": "Bachweg",
        },
        "Zaku Altdorf dag": {
            "service_provider": "zaku",
            "municipality": "Altdorf",
            "street": "dag",
        },
    }

    PARAMS = (
        dropdown("service_provider", list(SERVICES), label="Service provider"),
        municipality(),
        street(optional=True),
        house_number("hnr", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose the waste association (`service_provider`) and enter your "
            "municipality as the association's calendar writes it. A municipality "
            "divided by street also needs `street` (and `hnr` for long streets); "
            "one divided into collection areas needs the area's name or "
            "abbreviation as `street`. The error message lists the valid values."
        ),
    }

    retrieve = calendar_retriever(
        lambda *_, service_provider, **__: SERVICES[service_provider]["search"],
        lambda *_, service_provider, **__: SERVICES[service_provider]["collections"],
    )
    parse = parsers.EachResponse(
        parsers.JsonParser(),
        then=preprocessors.ExplodeList(split_types, into="type"),
    )
    transform = JsonTransformer(
        date_key="DATUM",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=_TYPE_MAP,
    )
