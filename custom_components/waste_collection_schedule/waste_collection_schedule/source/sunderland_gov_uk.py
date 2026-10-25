import json
import re
from datetime import datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.GossForm import GossJsonParser
from waste_collection_schedule.service.HtmlForms import FormStep, HtmlFormRetriever
from waste_collection_schedule.transformers import RowTransformer

_PREFIX = "BINCOLLECTIONCHECKERNEWV3"
_ACTION = f"{_PREFIX}_FORMACTION_NEXT"
_POSTCODE = f"{_PREFIX}_ADDRESSSEARCH_SCCPOSTCODE"
_ADDRESSES = f"{_PREFIX}_ADDRESSSEARCH_SCCLISTOFADDRESSES"
_TRIGGER = f"{_PREFIX}_ADDRESSSEARCH_POSTCODETRIGGER"


def _normalise(value):
    return " ".join(re.sub(r"[^\w]+", " ", str(value)).split()).casefold()


def _address_fields(response, postcode, address, **_):
    page = BeautifulSoup(response.text, "html.parser")
    addresses = [
        (str(option.get("value") or "").strip(), option.get_text(" ", strip=True))
        for option in page.select(f'select[name="{_ADDRESSES}"] option')
        if option.get("value")
    ]
    if not addresses:
        raise SourceArgumentNotFoundWithSuggestions("postcode", postcode, [])
    requested = _normalise(address)
    matches = [
        (value, label) for value, label in addresses if _normalise(label) == requested
    ]
    if not matches and requested:
        matches = [
            (value, label)
            for value, label in addresses
            if requested in _normalise(label)
        ]
    if len(matches) != 1:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, [label for _, label in addresses]
        )
    uprn, label = matches[0]
    return {
        _ADDRESSES: uprn,
        f"{_PREFIX}_ADDRESSSEARCH_POSTCODE": postcode,
        f"{_PREFIX}_ADDRESSSEARCH_UPRN": uprn,
        f"{_PREFIX}_ADDRESSSEARCH_ADDRESSTEXT": label,
        _ACTION: _TRIGGER,
    }


def _label(label):
    for keyword, key in (
        ("garden", "garden"),
        ("recycl", "recycling"),
        ("blue", "recycling"),
        ("bulky", "bulky"),
        ("household", "general"),
        ("green", "general"),
        ("residual", "general"),
        ("refuse", "general"),
        ("waste", "general"),
    ):
        if keyword in label.casefold():
            return key
    return label


def _rows(record, source):
    raw = record.get("DATARETURNED")
    if not raw:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", source.params.get("address") if source else "", []
        )
    value = json.loads(raw) if isinstance(raw, str) else raw
    result = value.get("result", value)
    rows = {}
    for schedule in result.get("schedules", []):
        if str(schedule.get("status", "")).upper() != "IN SERVICE":
            continue
        label = schedule.get("binName") or schedule.get("jobName") or "Bin Collection"
        for value in schedule.get("futureJobs", []):
            if not value:
                continue
            try:
                day = datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
            except ValueError:
                continue
            rows[(day, label)] = (day, label)
    return sorted(rows.values(), key=lambda row: row[0])


@final
class Source(BaseSource):
    TITLE = "Sunderland City Council"
    DESCRIPTION = "Source for Sunderland City Council bin collection schedules."
    URL = "https://www.sunderland.gov.uk/bindays?ccp=true"
    COUNTRY = "uk"
    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "SR4 7PU", "address": "191 Cleveland Road"},
        "Test_002": {"postcode": "SR3 2DW", "address": "43 Hill Street"},
        "Test_003": {"postcode": "SR4 8RJ", "address": "17 Sutherland Drive"},
    }
    PARAMS = (postcode(), street_address())
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Enter the postcode and property address from the Sunderland bin day checker. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = HtmlFormRetriever(
        "https://www.sunderland.gov.uk/bindays?ccp=true",
        steps=(
            FormStep(
                form=f'input[name="{_POSTCODE}"]',
                argument="postcode",
                button=_ACTION,
                redirects=True,
                fields=lambda response, postcode, **_: {
                    _POSTCODE: re.sub(r"\s+", " ", str(postcode).strip().upper()),
                    _ACTION: _TRIGGER,
                },
            ),
            FormStep(
                form=f'select[name="{_ADDRESSES}"]',
                argument="address",
                redirects=True,
                fields=lambda response, postcode, address, **_: _address_fields(
                    response,
                    re.sub(r"\s+", " ", str(postcode).strip().upper()),
                    address,
                ),
            ),
        ),
    )
    parse = GossJsonParser("ADDRESSSEARCH_1")
    preprocess = preprocessors.ExplodeList(_rows)
    transform = RowTransformer(
        clean=_label,
        type_value_map={
            "general": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
            "bulky": wt.BULKY_WASTE,
        },
    )
