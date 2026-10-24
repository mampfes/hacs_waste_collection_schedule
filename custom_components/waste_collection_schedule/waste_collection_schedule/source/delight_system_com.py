from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    municipality,
    text_field,
)
from waste_collection_schedule.service.ThreeR import (
    LANGUAGE_CODES,
    ThreeRCalendarParser,
    ThreeRRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# The ThreeR app's whole conversation (municipality, area tree, throwaway user,
# calendar) is the platform's, in ``service/ThreeR.py``.


@final
class Source(BaseSource):
    TITLE = "ThreeR"
    DESCRIPTION = (
        "Source for Japanese municipalities using the ThreeR garbage collection app."
    )
    URL = "https://threer1.delight-system.com"
    COUNTRY = "jp"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Shinjuku Aizumi-cho (by municipality id)": {
            "municipality": "shinjukuku",
            "area_name": "Aizumi-cho",
            "language_code": "en",
        },
        "Shinjuku Aizumi-cho (by municipality name)": {
            "municipality": "Shinjuku City",
            "area_name": "Aizumi-cho",
            "language_code": "en",
        },
        "Shinjuku Okubo 1 chome (town / chome)": {
            "municipality": "shinjukuku",
            "area_name": "Okubo / 1 chome",
            "language_code": "en",
        },
        "Osaka Kita ward Ukita 1-chome 2-ban 2-5 go (ward / chome / ban / go)": {
            "municipality": "大阪市",
            "area_name": "北区 / 浮田1丁目 / 2番 / 2～5号",
            "language_code": "ja",
        },
    }

    PARAMS = (
        dropdown("language_code", LANGUAGE_CODES, "Language"),
        municipality(),
        text_field("area_name", "Area name"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality and neighbourhood exactly as shown in the "
            "ThreeR garbage app (e.g. municipality `Shinjuku City`, area "
            "`Aizumi-cho`). Where the app asks for several levels, enter all of "
            "them, separated by ` / ` (e.g. `Okubo / 1 chome`). If a value is not "
            "recognised, the setup form will offer matching options from the "
            "live API."
        ),
    }

    retrieve = ThreeRRetriever()
    parse = ThreeRCalendarParser()
    transform = RowTransformer()
