"""West Lothian Council (westlothian.gov.uk).

Demonstrates: a GOSS-forms-driven flow, which is ``IcsSessionRetriever`` with
two steps and no separate feed request. The first step scrapes the bin
collection form's action URL and the session ids embedded in its query string;
the second POSTs the postcode/UPRN back to that URL, and the page it answers
with *is* the calendar, so ``feed_url`` stays ``None`` and the last step's
response is what the parser reads. The form is a rolling lookup rather than a
per-year calendar, hence ``lookahead_month=None``.

The result page carries the schedule as a base64+JSON blob inside a
``<script>`` tag, which is exactly what ``IcsFeedsParser(unwrap=...)`` is for.
Which blob holds it depends on whether the council's own ICS generation
succeeded that day: normally ``WLBINCOLLECTIONSerializedVariables`` carries the
iCalendar document, and when that errors the plain-JSON
``WLBINCOLLECTIONFormData`` blob on the same page still lists each bin's next
collection. ``_calendar_text`` reads whichever is available and returns
iCalendar either way, so one pipeline covers both.

The malformed RRULE UNTIL this council emits (a bare date against a
date-with-time DTSTART, see #7046) is no longer patched here: it is one of the
shared repairs in ``service/ICS.py``, applied to every provider on the
platform.
"""

import base64
import json
import re
from typing import Any, ClassVar, final
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_COLLECTION_PAGE_URL = "https://www.westlothian.gov.uk/bin-collections"

_ICAL_VAR_RE = re.compile(
    r'var WLBINCOLLECTIONSerializedVariables = "(.*?)";$', re.MULTILINE | re.DOTALL
)
_FORMDATA_VAR_RE = re.compile(
    r'var WLBINCOLLECTIONFormData = "(.*?)";$', re.MULTILINE | re.DOTALL
)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Sec-Fetch-Dest": "document",
    "Host": "www.westlothian.gov.uk",
    "Sec-Fetch-User": "?1",
    "Accept-Language": "en-GB,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "westlothian.gov.uk",
    "Cache-Control": "no-cache",
    "DNT": "1",
}


def _goss_form(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """The form's action URL and the GOSS session ids held in its query."""
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find(id="WLBINCOLLECTION_FORM")
    if not isinstance(form, Tag):
        raise SourceArgumentException(
            "postcode", "could not find the bin collection form on the page"
        )
    action_url = str(form["action"])
    values = parse_qs(urlparse(action_url).query)
    return {
        "action_url": action_url,
        "page_session_id": values["pageSessionId"][0],
        "session_id": values["fsid"][0],
        "nonce": values["fsn"][0],
    }


def _submission(
    page_session_id: str,
    session_id: str,
    nonce: str,
    uprn: str,
    postcode: str,
    **_,
) -> "dict[str, str]":
    return {
        "WLBINCOLLECTION_PAGESESSIONID": page_session_id,
        "WLBINCOLLECTION_SESSIONID": session_id,
        "WLBINCOLLECTION_NONCE": nonce,
        "WLBINCOLLECTION_VARIABLES": "e30=",
        "WLBINCOLLECTION_PAGENAME": "PAGE1",
        "WLBINCOLLECTION_PAGEINSTANCE": "0",
        "WLBINCOLLECTION_PAGE1_UPRN": str(uprn),
        "WLBINCOLLECTION_PAGE1_ADDRESSLOOKUPPOSTCODE": postcode,
        "WLBINCOLLECTION_PAGE1_ADDRESSLOOKUPADDRESS": "4",
        "WLBINCOLLECTION_FORMACTION_NEXT": "WLBINCOLLECTION_PAGE1_NAVBUTTONS",
    }


def _extract_serialized(html: str, pattern: "re.Pattern[str]") -> "dict | None":
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", string=pattern)
    if not script:
        return None
    match = pattern.search(script.text)
    if not match:
        return None
    return json.loads(base64.b64decode(match.group(1)))


def _calendar_from_collections(collections: str) -> str:
    """Render the plain-JSON bin list as the calendar the site failed to build.

    Each entry names a bin and the date of its next collection, which is the
    same ``(date, bin)`` pair the iCalendar blob would have carried, so writing
    it out as all-day VEVENTs keeps one parse path for both shapes of the page.
    """
    events = "".join(
        "BEGIN:VEVENT\r\n"
        f"UID:{entry['nextCollectionISO']}-{entry['binType']}@westlothian.gov.uk\r\n"
        f"DTSTART;VALUE=DATE:{entry['nextCollectionISO'].replace('-', '')}\r\n"
        f"SUMMARY:{entry['binType']}\r\n"
        "END:VEVENT\r\n"
        for entry in json.loads(collections)
    )
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
        "PRODID:-//waste_collection_schedule//westlothian_gov_uk//EN\r\n"
        f"{events}END:VCALENDAR\r\n"
    )


def _calendar_text(body: str) -> str:
    """The iCalendar document the result page embeds, from whichever blob has it."""
    info = _extract_serialized(body, _ICAL_VAR_RE)
    if info is None:
        raise SourceArgumentException(
            "postcode", "could not find bin collection data on the result page"
        )

    ical_content = info.get("ICALCONTENT")
    if isinstance(ical_content, dict) and ical_content.get("error") is not None:
        # West Lothian's own ICS generation failed today; fall back to the
        # plain-JSON blob the same result page also embeds.
        form_data = _extract_serialized(body, _FORMDATA_VAR_RE) or {}
        webpage_content = form_data.get("PAGE2_1")
        if webpage_content is None:
            raise SourceArgumentException("postcode", "no entries could be parsed")
        return _calendar_from_collections(webpage_content["COLLECTIONS"])

    if ical_content is None:
        raise SourceArgumentException("postcode", "no entries could be parsed")
    if ical_content.get("error") is not None:
        raise SourceArgumentException("postcode", ical_content["error"])
    return ical_content["value"]


@final
class Source(BaseSource):
    TITLE = "West Lothian Council"
    DESCRIPTION = "Source for services for West Lothian"
    URL = "https://www.westlothian.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "EH48+4DD", "uprn": "135007799"},
        "Test_002": {"postcode": "EH55+8FJ", "uprn": "135051417"},
    }

    PARAMS = (postcode(postcode_field="postcode"), uprn())

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "url": _COLLECTION_PAGE_URL,
                "headers": _HEADERS,
                "extract": _goss_form,
            },
            {
                "method": "POST",
                "url": lambda action_url, **_: action_url,
                "data": _submission,
                "headers": _HEADERS,
            },
        ],
        # The submission answers with the result page itself, so there is no
        # separate calendar download to follow.
        feed_url=None,
        lookahead_month=None,
    )

    parse = IcsFeedsParser(parsers.IcsParser(), unwrap=_calendar_text)

    # Verified live against the council's own bin-sorting guidance
    # (westlothian.gov.uk): grey = general household waste, brown = food +
    # garden waste, green = plastics/metal/cans recycling, blue = paper and
    # card. The legacy ICON_MAP had green/blue backwards (GLASS/EVENT); this
    # corrects that rather than preserving the mistake.
    transform = ICSTransformer(
        type_value_map={
            "grey": wt.GENERAL_WASTE,
            "brown": wt.ORGANIC,
            "green": wt.RECYCLABLES,
            "blue": wt.PAPER,
        }
    )
