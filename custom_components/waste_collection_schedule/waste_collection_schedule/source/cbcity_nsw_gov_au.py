from typing import ClassVar, final

from waste_collection_schedule import preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.CanterburyBankstown import CalendarParser, assets
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "City of Canterbury-Bankstown (NSW)"
    DESCRIPTION = "City of Canterbury-Bankstown bin day finder"
    URL = "https://bindayfinder.azurewebsites.net"
    TEST_CASES: ClassVar[dict] = {
        "Tab 1 Zone A": {"address": "102 Crinan Street, Hurlstone Park 2193"},
        "Tab 1 Zone B": {"address": "1 / 1 Aster Avenue, Punchbowl 2196"},
        "Tab 2a": {"address": "1 / 1 Bellevue Avenue, Lakemba 2195"},
        "Tab 2b": {"address": "1 / 1 Carysfield Road, Bass Hill 2197"},
        "Tab 2c": {"address": "1 / 1 Carmen Street, Bankstown 2200"},
        "Tab 3": {"address": "1 / 1 Fabos Place, Croydon Park 2133"},
        "Tab 4": {"address": "1 / 1 Charles Street, Canterbury 2193"},
        "Tab 5": {"address": "1 / 7 Cross Street, Bankstown 2200"},
        "Tab 6": {"address": "32 Kitchener Parade, Bankstown 2200"},
        "Address without comma": {"address": "102 Crinan Street Hurlstone Park 2193"},
        "Address with state": {"address": "102 Crinan Street, Hurlstone Park NSW 2193"},
        "Address with state spelled out": {
            "address": "102 Crinan Street, Hurlstone Park New South Wales 2193"
        },
        "Address with abbreviated street type": {
            "address": "102 Crinan St Hurlstone Park"
        },
    }
    COUNTRY = "au"
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "zzzznotreal"},
        "Ambiguous address": {"address": "102"},
    }
    PARAMS = (street_address(),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your full Canterbury-Bankstown property address, e.g. '102 Crinan Street, Hurlstone Park 2193'. Address punctuation, NSW and common abbreviated street types are accepted. The current published web application supplies the cycle anchor and address-specific bin model. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Request("https://bindayfinder.azurewebsites.net"),
        targets=assets,
        fetch=retrievers.Request(lambda target, response, **_: target),
    )
    parse = CalendarParser()
    preprocess = preprocessors.Compose(
        preprocessors.RecurrenceExpander(lambda schedule, _: (schedule,)),
        preprocessors.SortRows(),
    )
    transform = RowTransformer(
        type_value_map={
            "red": wt.GENERAL_WASTE,
            "yellow": wt.RECYCLABLES,
            "green": wt.ORGANIC,
        }
    )
