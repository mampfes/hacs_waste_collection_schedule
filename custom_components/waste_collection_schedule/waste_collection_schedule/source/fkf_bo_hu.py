from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, street
from waste_collection_schedule.service.OctoberCms import handler
from waste_collection_schedule.transformers import RowTransformer

# The page lives on the bare host: "www." redirects to it, and a redirected POST
# turns into a GET that answers the whole page instead of the handler's JSON.
_URL = "https://mohubudapest.hu/hulladeknaptar-budaors"
_PARTIAL = "ajax/budaorsResults"


@final
class Source(BaseSource):
    TITLE = "FKF Budaörs"
    DESCRIPTION = "Source script for www.fkf.hu"
    URL = "https://www.fkf.hu"
    COUNTRY = "hu"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_1": {"street": "Templom tér"},
        "Test_2": {"street": "Völgy utca"},
        "Test_3": {"street": "Zombori utca"},
    }

    PARAMS = (
        street(),
        # Kept so configurations that set it keep loading; certificates are
        # always verified now.
        boolean("ssl_verify", default=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street as the calendar's street list at "
            "https://www.mohubudapest.hu/hulladeknaptar-budaors writes it. "
            "`ssl_verify` is no longer used."
        ),
    }

    retrieve = handler(
        _URL, "onSearch", _PARTIAL, lambda street, **_: {"publicPlace": street}
    )
    # A row per day: weekday, date, and a div per service collected that day.
    parse = parsers.HtmlLabelledDates(
        "tr",
        label="td div",
        date="td:nth-of-type(2)",
        date_pattern=r"(\d{4}\.\d{2}\.\d{2})",
        all_labels=True,
        from_json_key=_PARTIAL,
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y.%m.%d"),
        type_value_map={
            "Kommunális": wt.GENERAL_WASTE,
            "Szelektív": wt.RECYCLABLES,
            "Zöld": wt.GARDEN_WASTE,
        },
    )
