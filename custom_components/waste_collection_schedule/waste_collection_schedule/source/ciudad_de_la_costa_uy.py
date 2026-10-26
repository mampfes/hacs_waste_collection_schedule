from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import preprocessors, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.KmlZones import KmlWeekdayZoneParser
from waste_collection_schedule.transformers import RowTransformer


def _schedule(record, source):
    today = date.today()
    return [
        preprocessors.Schedule(
            key=record["type"],
            start=recurrence.next_weekday(record["weekday"], on_or_after=today),
            not_before=today,
            until=today + timedelta(days=59),
        )
    ]


@final
class Source(BaseSource):
    TITLE = "Municipio de Ciudad de la Costa"
    DESCRIPTION = "Source for household waste (general and recyclables) collection in Ciudad de la Costa, Canelones, Uruguay."
    URL = "https://www.imcanelones.gub.uy"
    COUNTRY = "uy"
    TEST_CASES: ClassVar[dict] = {
        "De los Pinos, Lomas de Solymar": {
            "address": "De los Pinos, Ciudad de la Costa"
        },
        "Cuba, Parque de Carrasco": {"address": "1901 Cuba, Ciudad de la Costa"},
        "Guillermo Perez Butler, El Pinar": {
            "address": "1944 Avenida Guillermo Perez Butler, Ciudad de la Costa"
        },
    }
    PARAMS = (street_address(),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address in Ciudad de la Costa. Include the neighbourhood for common street names. The published municipal zone map supplies collection weekdays. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Request(
            "https://nominatim.openstreetmap.org/search",
            params=lambda address, **_: {
                "q": f"{address.strip()}, Ciudad de la Costa, Canelones, Uruguay",
                "format": "json",
                "limit": "1",
                "countrycodes": "uy",
            },
            headers={"User-Agent": "hacs_waste_collection_schedule"},
        ),
        targets=lambda source, response: (
            "https://www.google.com/maps/d/kml?mid=17F0VsWkN9V7hoqMSyQ_H2_rl0SYLlZel&forcekml=1",
        ),
        fetch=retrievers.Request(lambda target, response, **_: target),
        include_prepared=True,
    )
    parse = KmlWeekdayZoneParser(
        folder="RESIDUOS",
        groups={
            "general": r"MEZCLADOS\s*\(([^)]+)\)",
            "recycling": r"RECICLABLES\s*\(([^)]+)\)",
        },
        weekdays={
            "LUNES": 0,
            "MARTES": 1,
            "MIERCOLES": 2,
            "JUEVES": 3,
            "VIERNES": 4,
            "SABADO": 5,
            "DOMINGO": 6,
        },
    )
    preprocess = preprocessors.Compose(
        preprocessors.RecurrenceExpander(_schedule), preprocessors.SortRows()
    )
    transform = RowTransformer(
        type_value_map={"general": wt.GENERAL_WASTE, "recycling": wt.RECYCLABLES}
    )
