import datetime
from typing import TypedDict, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import api_key, uprn
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Demonstrates: the config_params.api_key() PARAM on the BaseSource pipeline.
#
# Leeds publishes bin days through an Azure API Management endpoint that is keyed
# by an ocp-apim-subscription-key header. The key is embedded (shipped
# client-side) in the council's own public bin-day web app, so it is freely
# obtainable rather than a login credential. We default it to that embedded
# value so users normally only supply their UPRN, while still exercising the
# api_key() PARAM and letting a user override the key if the council rotates it.
#
# The API also needs a start/end date window. That is computed at fetch time
# (today .. +8 weeks) rather than asked of the user, so the only required user
# input is the UPRN. A small retrieve() method injects the header and the
# computed window; parse + a JsonTransformer handle the flat {type, date} array.

API_URL = "https://api.leeds.gov.uk/public/waste/v1/BinsDays"

# Embedded public subscription key from the council's own bin-day web app.
# Not a login: the same value is shipped to every visitor's browser.
DEFAULT_API_KEY = "ad8dd80444fe45fcad376f82cf9a5ab4"

# How far ahead to request collections.
WINDOW_DAYS = 56


class _Collection(TypedDict):
    """The fields the transformer reads from each BinsDays entry."""

    type: str
    date: str


@final
class Source(BaseSource):
    TITLE = "Leeds City Council"
    DESCRIPTION = "Source for Leeds City Council bin collections."
    URL = "https://www.leeds.gov.uk/bins-and-recycling"
    COUNTRY = "uk"
    CODEOWNERS = ["@markvp"]
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Rose Terrace LS18": {"uprn": "72306030"},
        "Greenside Drive LS12": {"uprn": "72083396"},
        "Vicarage View LS5": {"uprn": "72543283"},
    }

    PARAMS = [uprn(), api_key(default=DEFAULT_API_KEY)]

    HOWTO = {
        "en": (
            "Provide your UPRN (Unique Property Reference Number); find it at "
            "https://www.findmyaddress.co.uk/. The API Key is optional: leave it "
            "blank to use the council's embedded public key, and only set it if "
            "the council rotates the key."
        ),
    }

    _TYPE_MAP = {
        "Black": GENERAL_WASTE,
        "Green": RECYCLABLES,
        "Brown": GARDEN_WASTE,
    }

    parse = parsers.JsonParser(shape=list[_Collection])

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map=_TYPE_MAP,
    )

    def __init__(self, uprn=None, api_key=None):
        # api_key defaults to the embedded public key via apply_defaults().
        super().__init__(uprn=uprn, api_key=api_key)

    def retrieve(self, source):
        today = datetime.date.today()
        end = today + datetime.timedelta(days=WINDOW_DAYS)
        return source.session.get(
            API_URL,
            params={
                "uprn": source.params["uprn"],
                "startDate": today.isoformat(),
                "endDate": end.isoformat(),
            },
            headers={"ocp-apim-subscription-key": source.params["api_key"]},
            timeout=source.TIMEOUT,
        )
