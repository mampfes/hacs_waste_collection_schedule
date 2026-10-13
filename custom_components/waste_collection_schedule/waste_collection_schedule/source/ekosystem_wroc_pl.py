from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Wrocław"
    DESCRIPTION = "Source for ekosystem.wroc.pl for Wrocław, Poland"
    URL = "https://ekosystem.wroc.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit the Ekosystem schedule search "
            "(https://ekosystem.wroc.pl/gospodarowanie-odpadami/harmonogram-wywozu-odpadow/), "
            "search for your address and get the schedule. The URL contains your "
            "location id as the parameter `lokalizacja`."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Legnicka 160": {"location_id": 650358},
        "Marcepanowa 7": {"location_id": 680085},
    }

    PARAMS: ClassVar[list] = [location_id()]

    retrieve = Request(
        "https://ekosystem.wroc.pl/wp-admin/admin-ajax.php",
        method="POST",
        data=lambda location_id, **_: {
            "action": "waste_disposal_form_get_schedule",
            "id_numeru": location_id,
        },
    )
    parse = parsers.HtmlColumnDates(from_json_key="wiadomoscRWD")
    transform = ICSTransformer(
        type_value_map={
            "zmieszane": wt.GENERAL_WASTE,
            "tworzywa": wt.RECYCLABLES,
            "BIO": wt.ORGANIC,
            "papier": wt.PAPER,
            "szkło": wt.GLASS,
        },
    )
