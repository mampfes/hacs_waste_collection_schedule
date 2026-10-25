from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://www.geelongaustralia.com.au/recycling/calendar/default.aspx"
_STATE_FIELDS = ("__VIEWSTATE", "__EVENTVALIDATION")


def _form(response, **_):
    fields = retrievers.form_inputs(response.text, required=_STATE_FIELDS)
    return response.url, {name: fields[name] for name in _STATE_FIELDS}


def _bin_type(element):
    heading = element.find_previous("h3", class_="heading-icon")
    return heading.get_text().split(" (", 1)[0] if heading is not None else ""


@final
class Source(BaseSource):
    TITLE = "City of Greater Geelong"
    DESCRIPTION = "Source City of Greater Geelong rubbish collection"
    URL = "https://www.geelongcity.vic.gov.au/"
    COUNTRY = "au"

    TEST_CASES: ClassVar[dict] = {
        "155 Mercer Street Geelong 3220": {"address": "155 Mercer Street Geelong 3220"},
        "1/271 Roslyn Road Highton 3216": {"address": "1/271 Roslyn Road Highton 3216"},
        "1a Orton Street Ocean Grove 3226": {
            "address": "1a Orton Street Ocean Grove 3226"
        },
        "100-102 Gheringhap Street Geelong 3220": {
            "address": "100-102 Gheringhap Street Geelong 3220"
        },
    }
    PARAMS = (street_address(),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as accepted by the council's calendar search: "
            "https://www.geelongaustralia.com.au/recycling/calendar.aspx"
            ". Since the v3 pipeline migration, waste types use canonical, localised "
            "names. Update filters, automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = retrievers.Request(
        lambda form, **_: form[0],
        method="POST",
        before=(retrievers.Lookup(API_URL, pick=_form),),
        data=lambda form, address, **_: {
            "ctl00$ContentBody$BTN_SEARCH": "Search",
            "ctl00$ContentBody$TB_SEARCH": address,
            **form[1],
        },
    )
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser(
            "#ctl00_ContentBody_P_CALENDAR .read-text ul li",
            require=["#ctl00_ContentBody_P_CALENDAR .read-text"],
        ),
        argument="address",
        matches=lambda response, source: (
            "We couldn't find a match for" not in response.text
        ),
        hint=(
            "No collection calendars are available for this property. Check the "
            f"address against the council's own search ({API_URL})."
        ),
    )
    transform = HtmlTransformer(
        date_getter=lambda element: element.get_text(strip=True),
        type_getter=_bin_type,
        parse_date=date_parsers.for_format("%A, %d %B %Y"),
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green waste": wt.GARDEN_WASTE,
        },
    )
