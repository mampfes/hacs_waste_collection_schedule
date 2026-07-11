"""West Lothian Council (westlothian.gov.uk).

Demonstrates: a GOSS-forms-driven flow (scrape the bin-collection form's
action URL and its embedded session ids, POST the postcode/UPRN, follow the
redirect) whose result page embeds its data as a base64+JSON blob inside a
``<script>`` tag under one of two different variable names depending on
whether the site's own ICS generation succeeded that day. No configured
retriever/parser expresses either the GOSS handshake or the "prefer the ICS
blob, fall back to the plain-JSON blob" branch, hence a source-defined
retrieve()/parse() pair. parse() normalises both shapes to the same
``(date, label)`` tuples so a single ICSTransformer types either one.
"""

import base64
import json
import re
from datetime import datetime
from typing import Any, ClassVar, final
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

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


def _goss_ids(action_url: str) -> dict:
    values = parse_qs(urlparse(action_url).query)
    return {
        "page_session_id": values["pageSessionId"][0],
        "session_id": values["fsid"][0],
        "nonce": values["fsn"][0],
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

    def retrieve(self, source):
        session = source.session
        postcode_value = source.params["postcode"]
        uprn = str(source.params["uprn"])

        address_page = session.get(_COLLECTION_PAGE_URL, headers=_HEADERS)
        address_page.raise_for_status()

        soup = BeautifulSoup(address_page.text, "html.parser")
        form = soup.find(id="WLBINCOLLECTION_FORM")
        goss_ids = _goss_ids(form["action"])

        response = session.post(
            form["action"],
            allow_redirects=True,
            headers=_HEADERS,
            data={
                "WLBINCOLLECTION_PAGESESSIONID": goss_ids["page_session_id"],
                "WLBINCOLLECTION_SESSIONID": goss_ids["session_id"],
                "WLBINCOLLECTION_NONCE": goss_ids["nonce"],
                "WLBINCOLLECTION_VARIABLES": "e30=",
                "WLBINCOLLECTION_PAGENAME": "PAGE1",
                "WLBINCOLLECTION_PAGEINSTANCE": "0",
                "WLBINCOLLECTION_PAGE1_UPRN": uprn,
                "WLBINCOLLECTION_PAGE1_ADDRESSLOOKUPPOSTCODE": postcode_value,
                "WLBINCOLLECTION_PAGE1_ADDRESSLOOKUPADDRESS": "4",
                "WLBINCOLLECTION_FORMACTION_NEXT": "WLBINCOLLECTION_PAGE1_NAVBUTTONS",
            },
        )
        response.raise_for_status()
        return response

    def parse(self, response, source=None) -> list:
        from waste_collection_schedule.service.ICS import ICS

        html = response.text
        info = _extract_serialized(html, _ICAL_VAR_RE)
        if info is None:
            raise SourceArgumentException(
                "postcode", "could not find bin collection data on the result page"
            )

        ical_content = info.get("ICALCONTENT")
        if isinstance(ical_content, dict) and ical_content.get("error") is not None:
            # West Lothian's own ICS generation failed today; fall back to the
            # plain-JSON blob the same result page also embeds.
            info = _extract_serialized(html, _FORMDATA_VAR_RE) or {}
            ical_content = info.get("ICALCONTENT")

        webpage_content = info.get("PAGE2_1")

        if ical_content is not None:
            if ical_content.get("error") is not None:
                raise SourceArgumentException("postcode", ical_content["error"])
            # The UNTIL values are date-only (UK-based) but lack a timezone,
            # which the ICS module requires for timezone-aware parsing.
            ics_data = re.sub(
                r"UNTIL=([0-9]+)",
                lambda m: "UNTIL=" + m.group(1) + "Z",
                ical_content["value"],
            )
            return ICS().convert(ics_data)

        if webpage_content is not None:
            collections = json.loads(webpage_content["COLLECTIONS"])
            entries: list[tuple[Any, str]] = []
            for c in collections:
                date = datetime.strptime(c["nextCollectionISO"], "%Y-%m-%d").date()
                entries.append((date, c["binType"]))
            return entries

        raise SourceArgumentException("postcode", "no entries could be parsed")

    # Verified live against the council's own bin-sorting guidance
    # (westlothian.gov.uk): grey = general household waste, brown = food +
    # garden waste, green = plastics/metal/cans recycling, blue = paper and
    # card. The legacy ICON_MAP had green/blue backwards (GLASS/EVENT); this
    # corrects that rather than preserving the mistake.
    transform = ICSTransformer(
        type_value_map={
            "grey": GENERAL_WASTE,
            "brown": ORGANIC,
            "green": RECYCLABLES,
            "blue": PAPER,
        }
    )

    def __init__(self, postcode: str, uprn: "str | int"):
        super().__init__(postcode=postcode, uprn=str(uprn))
