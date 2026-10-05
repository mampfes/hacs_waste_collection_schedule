import datetime
import logging
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import address, boolean
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_LOGGER = logging.getLogger(__name__)

_API = "https://api.fostplus.be/recyclecms/public/v1"
_HEADERS = {"x-consumer": "recycleapp.be", "User-Agent": ""}


def _zipcode_id(response, postcode, **_):
    items = [i for i in response.json()["items"] if i["available"]]
    if not items:
        raise SourceArgumentNotFound("postcode", postcode)
    return items[0]["id"]


def _street_id(response, zipcode_id, street, **_):
    items = response.json()["items"]
    if not items:
        raise SourceArgumentNotFound("street", street)
    for item in items:
        if item["name"].lower().strip() == street.lower().strip():
            return item["id"]
    _LOGGER.warning(
        "No exact street match found, using first result: %s", items[0]["name"]
    )
    return items[0]["id"]


def _keep(record, source):
    if "exception" in record and "replacedBy" in record["exception"]:
        return False
    if record["type"] == "event":
        return bool(source.params.get("add_events", True))
    return record["type"] == "collection"


_EVENT = "Event"


def _label(record):
    if record["type"] == "event":
        return _EVENT
    return record["fraction"]["name"]["en"]


def _description(record):
    if record["type"] == "event":
        return record["event"]["title"]["en"]
    return None


@final
class Source(BaseSource):
    TITLE = "Recycle!"
    DESCRIPTION = "Source for RecycleApp.be"
    URL = "https://www.recycleapp.be"
    COUNTRY = "be"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "3001, Waversebaan 276 with events": {
            "postcode": 3001,
            "street": "Waversebaan",
            "house_number": 276,
        },
        "3001, Waversebaan 276 without events": {
            "postcode": 3001,
            "street": "Waversebaan",
            "house_number": 276,
            "add_events": False,
        },
        "1400, Rue de namur 1 with events": {
            "postcode": 1400,
            "street": "Rue de namur",
            "house_number": 1,
            "add_events": True,
        },
        "3200 Th. De Beckerstraat 1": {
            "postcode": 3200,
            "street": "Th. De Beckerstraat",
            "house_number": 1,
        },
        "9180 Lokeren, Abelendreef 1": {
            "postcode": 9180,
            "street": "Abelendreef",
            "house_number": 1,
        },
        "8700 Abeelstraat 1": {
            "postcode": 8700,
            "street": "Abeelstraat",
            "house_number": 1,
        },
    }

    PARAMS = (
        address(),
        boolean("add_events", "Add events", default=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the postcode, street and house number as on "
            "https://www.recycleapp.be. Disable add_events to leave out "
            "events such as collection-point openings."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API}/zipcodes",
                params=lambda postcode, **_: {"q": postcode},
                headers=_HEADERS,
                pick=_zipcode_id,
            ),
            # The street search fails on the part of a name in front of a "."
            Lookup(
                f"{_API}/streets",
                method="POST",
                params=lambda zipcode_id, street, **_: {
                    "q": street.split(".")[-1],
                    "zipcodes": zipcode_id,
                },
                headers=_HEADERS,
                pick=_street_id,
            ),
        ),
        url=f"{_API}/collections",
        params=lambda zipcode_id, street_id, house_number, **_: {
            "zipcodeId": zipcode_id,
            "streetId": street_id,
            "houseNumber": house_number,
            "fromDate": datetime.date.today().isoformat(),
            "untilDate": (
                datetime.date.today() + datetime.timedelta(days=365)
            ).isoformat(),
            # the API pages at 20 items by default and rejects sizes above 200
            "size": 200,
        },
        headers=_HEADERS,
    )
    parse = JsonParser("items")
    preprocess = RowFilter(_keep)
    transform = JsonTransformer(
        date_key="timestamp",
        type_key=_label,
        # an event carries its title as the description
        description_key=_description,
        carry_raw_label=True,
        type_value_map={
            "Huisvuil": wt.GENERAL_WASTE,
            "Huisvuil DifTar": wt.GENERAL_WASTE,
            "Déchets ménagers résiduels": wt.GENERAL_WASTE,
            "Gft": wt.ORGANIC,
            "Gft-DifTar": wt.ORGANIC,
            "Groente, fruit- en tuinafval": wt.ORGANIC,
            "Paper-cardboard": wt.PAPER,
            "PMD": wt.RECYCLABLES,
            "Grofvuil (op afroep)": wt.BULKY_WASTE,
            "Snoeihout": wt.GARDEN_WASTE,
            "Snoeihout op aanvraag": wt.GARDEN_WASTE,
            "Tegeltaxi Leuven": wt.OTHER,
            _EVENT: wt.OTHER,
        },
    )
