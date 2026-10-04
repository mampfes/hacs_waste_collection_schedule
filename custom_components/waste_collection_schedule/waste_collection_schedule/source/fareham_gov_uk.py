import json
import re
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://www.fareham.gov.uk/internetlookups/search_data.aspx"
API_LIST = "DomesticBinCollections2025on"
GARDEN_KEY = "GardenWasteBinDay<br/>(seenotesabove)"
GARDEN_LABEL = "Garden Waste"

# "03/11/2025 (Refuse) and 10/11/2025 (Recycling)"
_COLLECTION = re.compile(r"(?P<date>\d{1,2}/\d{1,2}/\d{4}|today) \((?P<label>[^)]+)\)")
_DATE = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")


def _fix_json(text: str) -> str:
    """The council's JSON is malformed: stub rows and missing braces between rows."""
    rows_start = text.find('"rows": [')
    if rows_start == -1:
        return text
    prefix, rows = text[:rows_start], text[rows_start:]
    # Remove incomplete stub entries: { "Row": "N", immediately followed by another {
    rows = re.sub(r'\{\s*"Row":\s*"\d+",\s*(?=\{)', "", rows)
    # Add the missing { after "},", when the next token is a property key
    rows = re.sub(r"(},)(\s*)(\")", r"\1\2{\3", rows)
    return prefix + rows


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (value or "").lower())


def _squash(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _matching_rows(rows: list[dict], source) -> list[dict]:
    wanted_postcode = _squash(source.params["postcode"])
    road = source.params["road_name"]
    number = re.match(r"\s*(\d+[a-zA-Z]?)\s+(.+)", road)
    house, street_name = (number.group(1), number.group(2)) if number else (None, road)
    street_tokens = set(_tokens(street_name))
    matches = []
    for row in rows:
        address = row.get("Address", "")
        tokens = set(_tokens(address))
        if wanted_postcode not in _squash(address):
            continue
        if street_tokens and not street_tokens.issubset(tokens):
            continue
        if house and house.lower() not in tokens:
            continue
        matches.append(row)
    return matches


def _collections(text: str, source) -> list[tuple[date, str]]:
    """Every (date, label) of the rows matching the road and postcode, once each."""
    rows = json.loads(_fix_json(text)).get("data", {}).get("rows", [])
    if not rows:
        raise SourceArgumentNotFound(
            "postcode",
            source.params["postcode"],
            "please verify the postcode on recent council correspondence",
        )
    matches = _matching_rows(rows, source)
    if not matches:
        raise SourceArgumentNotFound(
            "road_name",
            source.params["road_name"],
            "please ensure it matches the selected postcode",
        )
    found: set[tuple[date, str]] = set()
    for row in matches:
        for match in _COLLECTION.finditer(row.get("BinCollectionInformation") or ""):
            if match.group("date") == "today":
                day = date.today()
            else:
                day = date_parsers.for_format("%d/%m/%Y")(match.group("date"))
            found.add((day, match.group("label")))
        garden = _DATE.search(row.get(GARDEN_KEY) or "")
        if garden:
            found.add(
                (date_parsers.for_format("%d/%m/%Y")(garden.group()), GARDEN_LABEL)
            )
    return sorted(found)


@final
class Source(BaseSource):
    TITLE = "Fareham Borough Council"
    DESCRIPTION = "Source for fareham.gov.uk"
    URL = "https://www.fareham.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "HUNTS_POND_ROAD": {"road_name": "Hunts pond road", "postcode": "PO14 4PL"},
        "CHRUCH_ROAD": {"road_name": "Church road", "postcode": "SO31 6LW"},
        "BRIDGE_ROAD": {"road_name": "Bridge road", "postcode": "SO31 7GD"},
        "SEGENSWORTH_ROAD": {
            "road_name": "203 Segensworth road",
            "postcode": "PO15 5EL",
        },
    }

    PARAMS = (street(field="road_name"), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your road name as listed by the council, "
            "optionally with your house number in front (e.g. '203 Segensworth "
            "road'). Without a house number the collections of all matching "
            "properties on the road are combined."
        ),
    }

    retrieve = HttpGetRetriever(
        url=API_URL,
        params=lambda postcode, **_: {
            "type": "JSON",
            "list": API_LIST,
            "Road or Postcode": postcode,
        },
    )
    parse = parsers.TextParser()
    preprocess = staticmethod(_collections)
    transform = ICSTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            GARDEN_LABEL: wt.GARDEN_WASTE,
        },
    )
