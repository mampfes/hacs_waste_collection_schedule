import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

VALID_ZONES = ["Kreis Ost", "Kreis West"]

_ZONE = re.compile(r"Zone:\s*(.+?)\s*$")
_DATE = re.compile(r"\d{2}\.\d{2}\.\d{4}")


def _description(item) -> str:
    return (item.findtext("description") or "").strip()


def _in_zone(item, source) -> bool:
    """Description format: "DD.MM.YYYY<br/>Zone: Kreis Ost"."""
    zone = _ZONE.search(_description(item))
    return bool(
        zone
        and _DATE.search(_description(item))
        and zone.group(1).strip() == source.params["zone"]
    )


def _date(item) -> str:
    match = _DATE.search(_description(item))
    return match.group(0) if match else ""


@final
class Source(BaseSource):
    TITLE = "Reinach BL"
    DESCRIPTION = (
        "Source for waste collection schedule of Gemeinde Reinach BL, Switzerland."
    )
    URL = "https://www.reinach-bl.ch"
    COUNTRY = "ch"
    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your collection zone (Kreis Ost or Kreis West). "
            "You can find your zone on the official Reinach BL waste calendar "
            "page at https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender."
        ),
        "de": (
            "Wählen Sie Ihren Abfuhrkreis (Kreis Ost oder Kreis West). "
            "Den Kreis finden Sie auf dem Abfallkalender der Gemeinde Reinach BL "
            "unter https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender."
        ),
    }
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kreis Ost": {"zone": "Kreis Ost"},
        "Kreis West": {"zone": "Kreis West"},
    }

    PARAMS = (dropdown("zone", VALID_ZONES),)

    retrieve = HttpGetRetriever(
        url="https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender/rss.php",
    )
    parse = parsers.XmlParser("channel/item")
    preprocess = preprocessors.RowFilter(_in_zone)
    transform = JsonTransformer(
        date_key=_date,
        type_key=lambda item: (item.findtext("title") or "").strip(),
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        type_value_map={
            "Hauskehricht": wt.GENERAL_WASTE,
            "Grünabfuhr/Bioabfall": wt.ORGANIC,
            "Häckseldienst": wt.GARDEN_WASTE,
            "Papier": wt.PAPER,
            "Karton": wt.PAPER,
            "Metalle": wt.OTHER,
        },
        carry_raw_label=True,
    )
