import base64
import json
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.GossForm import (
    GossFormRetriever,
    GossStep,
    GossWhitespaceParser,
)
from waste_collection_schedule.transformers import JsonTransformer

_FORM = "QUERYWARDSCOLLECTIONSWS"


def _fields(response, postcode, uprn, *, selected=False, **_):
    reference = str(uprn) if selected else ""
    variables = {"SEARCHREF": reference, "SEARCHUPRN": reference}
    return {
        "VARIABLES": base64.b64encode(json.dumps(variables).encode()).decode()
        if selected
        else "",
        "PAGENAME": "PAGE1",
        "PAGEINSTANCE": "0",
        "PAGE1_SEARCHED": "YES" if selected else "NO",
        "PAGE1_SEARCHADDRESS": "NO" if selected else "YES",
        "PAGE1_NEXTPAGE": "PAGE2",
        "PAGE1_POSTCODE": postcode,
        "PAGE1_PROPERTY": reference,
        "PAGE1_REFNO": reference,
        "PAGE1_UPRN": reference,
    }


@final
class Source(BaseSource):
    TITLE = "Gosport Borough Council"
    DESCRIPTION = "Source for Gosport Borough Council waste collection."
    URL = "https://www.gosport.gov.uk"
    COUNTRY = "uk"
    TEST_CASES: ClassVar[dict] = {
        "PO12 4RL, 1 Holland House": {"postcode": "PO12 4RL", "uprn": "37020212"},
        "PO12 2EL, 10 Testcombe Road": {"postcode": "PO12 2EL", "uprn": "37030710"},
    }
    PARAMS = (postcode(), uprn())
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://www.gosport.gov.uk/refuserecyclingdays, enter your postcode, "
            "and select your address. Use the Whitespace property reference shown "
            "next to your address in the dropdown as uprn. Since the v3 pipeline "
            "migration, waste types use canonical, localised names; update filters, "
            "automations and customisations using the old labels."
        ),
    }
    retrieve = GossFormRetriever(
        "https://www.gosport.gov.uk/refuserecyclingdays",
        form=_FORM,
        steps=(
            GossStep("PAGE1_GETADDRESSES", fields=_fields, argument="postcode"),
            GossStep(
                "PAGE1_FIELD9",
                fields=lambda response, **params: _fields(
                    response, selected=True, **params
                ),
            ),
        ),
    )
    parse = GossWhitespaceParser(_FORM)
    transform = JsonTransformer(
        date_key="Date",
        type_key="Service",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        type_value_map={
            "Domestic Waste Collection Service": wt.GENERAL_WASTE,
            "Recycling Waste Collection Service": wt.RECYCLABLES,
            "Garden Waste Collection Service": wt.GARDEN_WASTE,
        },
    )
