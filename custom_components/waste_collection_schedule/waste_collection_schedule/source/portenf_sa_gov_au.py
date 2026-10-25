import logging
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.service.AspNetForms import AspNetFormRetriever
from waste_collection_schedule.transformers import RowTransformer

_API = "https://ecouncil.portenf.sa.gov.au/public/propertywastedates/public.aspx"
_PREFIX = "ctl00$MainContent$"
_LOGGER = logging.getLogger(__name__)


def _post_data(
    response, suburb, street, house_number, unit_number="", *, selected=False, **_
):
    soup = BeautifulSoup(response.text, "html.parser")
    fields = {
        _PREFIX + "txtSuburb": suburb,
        _PREFIX + "txtStreetName": street,
        _PREFIX + "txtHouseNumber": str(house_number),
        _PREFIX + "txtUnitNumber": str(unit_number),
        "__EVENTTARGET": _PREFIX
        + ("gvPropertyResults$ctl02$btnSelect" if selected else "btnSearch"),
    }
    fields.update(retrievers.form_inputs(soup, hidden_only=True))
    if selected:
        choices = soup.find_all("a", {"class": "anchor-button small"}, string="Select")
        if not choices:
            raise ValueError("No address found")
        if len(choices) > 1:
            found = []
            for choice in choices:
                parent = choice.parent
                row = parent.parent if parent is not None else None
                if row is None:
                    raise ValueError("Address choice has no table row")
                found.append(
                    " ".join(
                        span.get_text()
                        for span in row.find_all("td")[1].find_all("span")
                    )
                )
            using_index = 0
            match = False
            for index, entry in enumerate(found):
                entry = entry.lower().strip().replace("  ", "")
                if all(
                    str(value).lower().strip().replace("  ", "") in entry
                    for value in (house_number, street, suburb, unit_number)
                ):
                    if match:
                        _LOGGER.warning(
                            "Multiple addresses found, using first one \nfound:%s%s \nusing:%s",
                            ", ".join(found[:10]),
                            "..." if len(found) >= 10 else "",
                            found[using_index],
                        )
                        break
                    using_index = index
                    match = True
            if not match:
                _LOGGER.warning(
                    "no perfect address match found, using:%s", found[using_index]
                )
        # Keep the first Select link, as in the existing WebForms flow.
        fields[str(choices[0]["href"]).split("'")[1]] = ""
    return fields


@final
class Source(BaseSource):
    TITLE = "Port Adelaide Enfield, South Australia"
    DESCRIPTION = "Source for City of Port Adelaide Enfield, South Australia."
    URL = "https://ecouncil.portenf.sa.gov.au/"
    COUNTRY = "au"
    TEST_CASES: ClassVar[dict] = {
        "Broadview, Regency Road, 565 ": {
            "suburb": "Broadview",
            "street": "Regency Road",
            "house_number": 565,
            "unit_number": "",
        },
        "48 Floriedale Rd ": {
            "suburb": "Greenacres",
            "street": "Floriedale Rd",
            "house_number": "48",
        },
        "24 Margaret Terrace": {
            "suburb": "Rosewater",
            "street": "Margaret Terrace",
            "house_number": "24",
        },
        "Addison Road 91 with unit": {
            "suburb": "Rosewater",
            "street": "Addison Road",
            "house_number": 91,
            "unit_number": 2,
        },
    }
    PARAMS = (
        text_field("suburb", "Suburb"),
        street(),
        house_number(),
        text_field("unit_number", "Unit number", default=""),
    )
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the suburb, street, house number and optional unit number as "
            "accepted by https://ecouncil.portenf.sa.gov.au/public/propertywastedates/public.aspx. "
            "Since the v3 pipeline migration, waste types use canonical, localised "
            "names; update filters, automations and customisations using the old labels."
        ),
    }
    retrieve = AspNetFormRetriever(
        _API,
        steps=(
            _post_data,
            lambda response, **params: _post_data(response, selected=True, **params),
        ),
    )
    parse = parsers.HtmlCalendarGrid(
        table="table.collection-day-calendar",
        header="th.header-month",
        day=".daynumber, .daynumber-empty",
        rolling=True,
        marker=".pickup .bin-container > div, .next-pickup .bin-container > div",
    )
    transform = RowTransformer(
        type_value_map={
            "general-waste": wt.GENERAL_WASTE,
            "organics": wt.ORGANIC,
            "recycling": wt.RECYCLABLES,
        }
    )
