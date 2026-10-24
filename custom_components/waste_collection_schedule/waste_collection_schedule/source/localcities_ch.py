from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.parsers import EachResponse
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Localcities import (
    CalendarParser,
    PlaceRows,
    calendar_retriever,
    calendar_url,
)
from waste_collection_schedule.transformers import ICSTransformer

_MUNICIPALITIES = (
    ("Volketswil", "https://www.volketswil.ch", "volketswil", "529"),
    ("Grenchen", "https://www.grenchen.ch", "grenchen", "3533"),
    ("Wangen bei Olten", "https://www.wangen-bei-olten.ch", "wangen-bei-olten", "3629"),
    ("Büren an der Aare", "https://www.bueren.ch", "bueren-an-der-aare", "849"),
    ("Liestal", "https://www.liestal.ch", "liestal", "3833"),
    ("Therwil", "https://www.therwil.ch", "therwil", "3757"),
    ("Beinwil am See", "https://www.beinwil-am-see.ch", "beinwil-am-see", "5313"),
    ("Monthey", "https://www.monthey.ch", "monthey", "8085"),
    ("Zofingen", "https://www.zofingen.ch", "zofingen", "5741"),
    ("Nidau", "https://www.nidau.ch", "nidau", "1561"),
    ("Rupperswil", "https://www.rupperswil.ch", "rupperswil", "5525"),
    ("Seegräben", "https://www.seegraeben.ch", "seegraeben", "349"),
    ("Solothurn", "https://www.stadt-solothurn.ch", "solothurn", "3625"),
)


@final
class Source(BaseSource):
    TITLE = "localcities.ch"
    DESCRIPTION = (
        "Source for waste collection schedules from localcities.ch (Switzerland)."
    )
    URL = "https://www.localcities.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.CARTONS,
        wt.PAPER,
        wt.GLASS,
        wt.METAL,
        wt.PLASTIC,
    ]

    REGIONS = tuple(
        region(title, url=url, municipality=slug, municipality_id=ident)
        for title, url, slug, ident in _MUNICIPALITIES
    )

    TEST_CASES: ClassVar[dict] = {
        "Volketswil - Hegnau": {
            "municipality": "volketswil",
            "municipality_id": "529",
            "zone": "Hegnau",
        },
        "Volketswil - Kindhausen, Zimikon, Gutenswil": {
            "municipality": "volketswil",
            "municipality_id": "529",
            "zone": "Kindhausen, Zimikon, Gutenswil",
        },
        "Grenchen - Zone Ost": {
            "municipality": "grenchen",
            "municipality_id": "3533",
            "zone": "Zone Ost",
        },
        "Grenchen - Zone West": {
            "municipality": "grenchen",
            "municipality_id": "3533",
            "zone": "Zone West",
        },
        "Büren an der Aare": {
            "municipality": "bueren-an-der-aare",
            "municipality_id": "849",
            "zone": "",
        },
        "Liestal - Kreis 1": {
            "municipality": "liestal",
            "municipality_id": "3833",
            "zone": "Kreis 1",
        },
        "Therwil": {
            "municipality": "therwil",
            "municipality_id": "3757",
            "zone": "",
        },
        "Beinwil am See (zoneless)": {
            "municipality": "beinwil-am-see",
            "municipality_id": "5313",
        },
        "Monthey (zoneless)": {
            "municipality": "monthey",
            "municipality_id": "8085",
        },
        "Zofingen": {
            "municipality": "zofingen",
            "municipality_id": "5741",
        },
        "Nidau - Römerstrasse": {
            "municipality": "nidau",
            "municipality_id": "1561",
            "zone": "Römerstrasse",
        },
        "Rupperswil": {
            "municipality": "rupperswil",
            "municipality_id": "5525",
        },
        "Seegräben": {
            "municipality": "seegraeben",
            "municipality_id": "349",
        },
        "Solothurn - Tour 1": {
            "municipality": "solothurn",
            "municipality_id": "3625",
            "zone": "Tour 1",
        },
    }

    PARAMS = (
        municipality(),
        text_field("municipality_id", "Municipality ID", coerce=str),
        text_field("zone", "Zone", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit your municipality's page on localcities.ch. The municipality "
            "name and ID are in the URL (e.g. /de/entsorgung/volketswil/529). The "
            "zone is shown next to each waste collection entry on the calendar. "
            "If your municipality does not use zones, omit the zone parameter."
        ),
        "de": (
            "Besuchen Sie die Seite Ihrer Gemeinde auf localcities.ch. Der "
            "Gemeindename und die ID sind in der URL (z.B. "
            "/de/entsorgung/volketswil/529). Die Zone wird neben jedem "
            "Entsorgungstermin angezeigt. Wenn Ihre Gemeinde keine Zonen "
            "verwendet, kann der Zone-Parameter weggelassen werden."
        ),
    }

    retrieve = calendar_retriever(
        lambda municipality, municipality_id, **_: calendar_url(
            municipality, municipality_id
        )
    )
    parse = EachResponse(CalendarParser())
    preprocess = PlaceRows("zone")
    transform = ICSTransformer(
        type_value_map={
            "Grünabfälle": wt.GARDEN_WASTE,
            "Karton": wt.CARTONS,
            "Altpapier": wt.PAPER,
            "Altglas": wt.GLASS,
            "Altmetall": wt.METAL,
            "Kunststoffe": wt.PLASTIC,
        }
    )
