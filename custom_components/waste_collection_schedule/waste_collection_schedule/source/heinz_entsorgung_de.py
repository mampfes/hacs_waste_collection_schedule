from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Heinz-Entsorgung (Landkreis Freising)"
    DESCRIPTION = "Source for Heinz-Entsorgung (Landkreis Freising) waste collection."
    URL = "https://abfallkalender.heinz-entsorgung.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_Freising": {
            "param": "yesJWYk53alJXaiMiOMJWYk53alJXagMnRlJXapNmbicCLvJnciQiOBJGblxncoNXYzVWZi4CLzJHdhJ3clNjIioWTv93c0Nici4CLqJWYyhjIiojMyASN9J"
        },
    }

    PARAMS = (text_field("param", "Location parameter"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://abfallkalender.heinz-entsorgung.de/ with the browser's "
            "developer tools (F12, Network tab), select your town and street, and "
            "copy the 'param' value of the request to "
            "api-enttermine.heinz-entsorgung.net/termine."
        ),
        "de": (
            "Öffnen Sie https://abfallkalender.heinz-entsorgung.de/ mit den "
            "Entwicklertools des Browsers (F12, Tab Netzwerk), wählen Sie Ort und "
            "Straße und kopieren Sie den 'param'-Wert der Anfrage an "
            "api-enttermine.heinz-entsorgung.net/termine."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://api-enttermine.heinz-entsorgung.net/termine",
        params=lambda param, **_: {"param": param},
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key="termin",
        type_key="fraktion",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        # The note ("nur 240", a bin size) is kept on the collection.
        description_key="zusatz",
        type_value_map={
            "BIO": wt.ORGANIC,
            "RM": wt.GENERAL_WASTE,
            "PPK": wt.PAPER,
            "GS": wt.RECYCLABLES,
        },
    )
