from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.BohdanecXlsxCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Lázně Bohdaneč"
    DESCRIPTION = "Source of city waste collection calendar (paper/plastic/mixed) of Lázně Bohdaneč."
    URL = "https://lazne.bohdanec.cz/svozovy%2Dkalendar/ms-2523"
    TEST_CASES: ClassVar[dict] = {"Lázně Bohdaneč": {}}
    HOWTO: ClassVar[dict] = {
        "en": 'By default no arguments are required. The integration will automatically\nretrieve the current XLSX link from the official city page (Lázně Bohdaneč\nwebsite, sections "Odpady" -> "Svozový kalendář").\n* If you want to pin the exact URL, open that page, click the XLSX download link,\n  copy the direct XLSX URL, and use it as `url`.\n* As a fallback you can download the file and use a local `file` path. Beware you need to manually upload file to HA.\n* If you enable dedicated calendars per waste type, set colors per calendar in the HA calendar UI.'
    }
    COUNTRY = "cz"
    PARAMS = (
        text_field("url", "Direct XLSX URL", optional=True),
        text_field("file", "Local XLSX file", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Komunální odpad": wt.GENERAL_WASTE,
            "Plast": wt.PLASTIC,
            "Papír": wt.PAPER,
        },
    )
