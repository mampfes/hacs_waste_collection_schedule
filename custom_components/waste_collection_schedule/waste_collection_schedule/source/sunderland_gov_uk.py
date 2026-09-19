import base64
import json
import re
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests

from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
)


TITLE = "Sunderland City Council"
DESCRIPTION = "Source for Sunderland City Council bin collection schedules."
URL = "https://www.sunderland.gov.uk/bindays?ccp=true"
COUNTRY = "uk"

TEST_CASES = {
    "Test_001": {"postcode": "SR4 7PU", "address": "191 Cleveland Road"},
    "Test_002": {"postcode": "SR3 2DW", "address": "43 Hill Street"},
    "Test_003": {"postcode": "SR4 8RJ", "address": "17 Sutherland Drive"},
}


BASE_URL = "https://www.sunderland.gov.uk"
BIN_DAYS_URL = f"{BASE_URL}/bindays?ccp=true"

FORM_PREFIX = "BINCOLLECTIONCHECKERNEWV3"

POSTCODE_FIELD = (
    f"{FORM_PREFIX}_ADDRESSSEARCH_SCCPOSTCODE"
)

ADDRESS_FIELD = (
    f"{FORM_PREFIX}_ADDRESSSEARCH_SCCLISTOFADDRESSES"
)

POSTCODE_TRIGGER = (
    f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODETRIGGER"
)

FORM_ACTION_NEXT = (
    f"{FORM_PREFIX}_FORMACTION_NEXT"
)

UPRN_FIELD = f"{FORM_PREFIX}_ADDRESSSEARCH_UPRN"

POSTCODE_RESULT_FIELD = (
    f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODE"
)

ADDRESS_TEXT_FIELD = (
    f"{FORM_PREFIX}_ADDRESSSEARCH_ADDRESSTEXT"
)

FORM_DATA_PATTERN = re.compile(
    r'BINCOLLECTIONCHECKERNEWV3FormData\s*=\s*"([^"]+)"'
)


ICON_MAP = {
    "RECYCLING": Icons.RECYCLING,
    "GENERAL WASTE": Icons.GENERAL_WASTE,
    "GARDEN WASTE": Icons.ORGANIC,
}


class Source:
    def __init__(self, postcode: str, **kwargs):
        self.postcode = postcode.strip().upper()

        self.session = requests.Session(
            impersonate="chrome"
        )

    @staticmethod
    def _normalise_postcode(postcode: str) -> str:
        postcode = re.sub(
            r"\s+",
            "",
            postcode.upper(),
        )

        if len(postcode) > 3:
            return f"{postcode[:-3]} {postcode[-3:]}"

        return postcode

    @staticmethod
    def _get_form_data(soup):
        postcode_input = soup.find(
            "input",
            {
                "name": POSTCODE_FIELD,
            },
        )

        if postcode_input is None:
            raise SourceArgumentNotFound(
                "postcode",
                "Sunderland postcode search form was not found.",
            )

        form = postcode_input.find_parent("form")

        if form is None:
            raise SourceArgumentNotFound(
                "postcode",
                "Sunderland postcode search form was not found.",
            )

        data = {}

        for element in form.find_all(
            [
                "input",
                "select",
                "textarea",
                "button",
            ]
        ):
            name = element.get("name")

            if not name:
                continue

            element_type = (
                element.get("type") or ""
            ).lower()

            if element_type in (
                "checkbox",
                "radio",
            ) and not element.has_attr("checked"):
                continue

            if element.name == "select":
                selected = element.find(
                    "option",
                    selected=True,
                )

                value = (
                    selected.get("value", "")
                    if selected
                    else ""
                )

            elif element.name == "textarea":
                value = element.text or ""

            else:
                value = element.get(
                    "value",
                    "",
                )

            if element.name == "button":
                if name != FORM_ACTION_NEXT:
                    continue

            data[name] = value

        return form, data

    def _follow_redirects(self, response):
        redirects = 0

        while response.is_redirect:
            redirects += 1

            if redirects > 10:
                raise SourceArgumentNotFound(
                    "postcode",
                    "Too many redirects while contacting Sunderland City Council.",
                )

            location = response.headers.get("Location")

            if not location:
                raise SourceArgumentNotFound(
                    "postcode",
                    "Sunderland City Council returned an invalid redirect.",
                )

            response = self.session.get(
                requests.compat.urljoin(
                    response.url,
                    location,
                ),
                timeout=30,
                allow_redirects=False,
            )

        return response

    def _submit_postcode(self, postcode: str):
        response = self.session.get(
            BIN_DAYS_URL,
            timeout=30,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        form, data = self._get_form_data(soup)

        data[POSTCODE_FIELD] = postcode
        data[FORM_ACTION_NEXT] = POSTCODE_TRIGGER

        action = form.get("action")

        if not action:
            raise SourceArgumentNotFound(
                "postcode",
                "Sunderland postcode form has no submission URL.",
            )

        response = self.session.post(
            requests.compat.urljoin(
                response.url,
                action,
            ),
            data=data,
            timeout=30,
            allow_redirects=False,
        )

        response = self._follow_redirects(response)

        response.raise_for_status()

        return BeautifulSoup(
            response.text,
            "html.parser",
        )

    def _find_address(self, soup):
        address_select = soup.find(
            "select",
            {
                "name": ADDRESS_FIELD,
            },
        )

        if address_select is None:
            raise SourceArgumentNotFound(
                "postcode",
                (
                    "We could not find any addresses for "
                    f"the postcode '{self.postcode}'."
                ),
            )

        options = address_select.find_all(
            "option"
        )

        addresses = []

        for option in options:
            value = option.get(
                "value",
                "",
            ).strip()

            if not value:
                continue

            text = option.get_text(
                " ",
                strip=True,
            )

            addresses.append(
                (
                    value,
                    text,
                )
            )

        if not addresses:
            raise SourceArgumentNotFound(
                "postcode",
                (
                    "We could not find any addresses for "
                    f"the postcode '{self.postcode}'."
                ),
            )

        # The WCS source currently receives only a postcode.
        # Sunderland's form requires an address/UPRN before it
        # exposes the collection schedule. Select the first valid
        # address returned for the postcode.
        return addresses[0]

    def _submit_address(
        self,
        soup,
        uprn: str,
        address: str,
    ):
        address_input = soup.find(
            "select",
            {
                "name": ADDRESS_FIELD,
            },
        )

        if address_input is None:
            raise SourceArgumentNotFound(
                "postcode",
                "Sunderland address selection form was not found.",
            )

        form = address_input.find_parent("form")

        if form is None:
            raise SourceArgumentNotFound(
                "postcode",
                "Sunderland address selection form was not found.",
            )

        data = {}

        for element in form.find_all(
            [
                "input",
                "select",
                "textarea",
                "button",
            ]
        ):
            name = element.get("name")

            if not name:
                continue

            element_type = (
                element.get("type") or ""
            ).lower()

            if element_type in (
                "checkbox",
                "radio",
            ) and not element.has_attr("checked"):
                continue

            if element.name == "select":
                selected = element.find(
                    "option",
                    selected=True,
                )

                value = (
                    selected.get("value", "")
                    if selected
                    else ""
                )

            elif element.name == "textarea":
                value = element.text or ""

            else:
                value = element.get(
                    "value",
                    "",
                )

            if element.name == "button":
                if name != FORM_ACTION_NEXT:
                    continue

            data[name] = value

        data[ADDRESS_FIELD] = uprn
        data[POSTCODE_RESULT_FIELD] = self.postcode
        data[UPRN_FIELD] = uprn
        data[ADDRESS_TEXT_FIELD] = address
        data[FORM_ACTION_NEXT] = POSTCODE_TRIGGER

        action = form.get("action")

        if not action:
            raise SourceArgumentNotFound(
                "postcode",
                "Sunderland address form has no submission URL.",
            )

        response = self.session.post(
            requests.compat.urljoin(
                response.url if "response" in locals() else BIN_DAYS_URL,
                action,
            ),
            data=data,
            timeout=30,
            allow_redirects=False,
        )

        response = self._follow_redirects(response)

        response.raise_for_status()

        return response

    @staticmethod
    def _decode_form_data(html: str):
        match = FORM_DATA_PATTERN.search(html)

        if not match:
            raise SourceArgumentNotFound(
                "postcode",
                (
                    "Sunderland City Council returned a page "
                    "without collection schedule data."
                ),
            )

        try:
            decoded = base64.b64decode(
                match.group(1)
            ).decode("utf-8")

            return json.loads(decoded)

        except (
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as err:
            raise SourceArgumentNotFound(
                "postcode",
                (
                    "Sunderland City Council returned "
                    "invalid collection schedule data."
                ),
            ) from err

    @staticmethod
    def _parse_date(value):
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                str(value).replace(
                    "Z",
                    "+00:00",
                )
            ).date()

        except ValueError:
            return None

    @classmethod
    def _create_collections(cls, data):
        schedules = (
            data.get("result", {})
            .get("schedules", [])
        )

        collections = []

        for schedule in schedules:
            collection_type = (
                schedule.get("type")
                or schedule.get("name")
                or schedule.get("description")
                or ""
            ).strip()

            if not collection_type:
                continue

            # Sunderland returns the actual future collection
            # dates in futureJobs. Do not rely on RESIDUALBIN,
            # RECYCLEBIN, etc., as those are only form variables.
            future_jobs = schedule.get(
                "futureJobs",
                [],
            )

            if not isinstance(
                future_jobs,
                list,
            ):
                continue

            icon = None

            normalized_type = collection_type.upper()

            for name, mapped_icon in ICON_MAP.items():
                if name in normalized_type:
                    icon = mapped_icon
                    break

            for job in future_jobs:
                if isinstance(job, dict):
                    date_value = (
                        job.get("date")
                        or job.get("collectionDate")
                        or job.get("collectionDateTime")
                        or job.get("dateTime")
                    )

                else:
                    date_value = job

                collection_date = cls._parse_date(
                    date_value
                )

                if collection_date is None:
                    continue

                collections.append(
                    Collection(
                        date=collection_date,
                        type=collection_type,
                        icon=icon,
                    )
                )

        return collections

    def fetch(self):
        postcode = self._normalise_postcode(
            self.postcode
        )

        address_page = self._submit_postcode(
            postcode
        )

        uprn, address = self._find_address(
            address_page
        )

        final_response = self._submit_address(
            address_page,
            uprn,
            address,
        )

        data = self._decode_form_data(
            final_response.text
        )

        collections = self._create_collections(
            data
        )

        if not collections:
            raise SourceArgumentNotFound(
                "postcode",
                (
                    "Sunderland City Council returned "
                    "no future bin collections for "
                    f"'{postcode}'."
                ),
            )

        # Remove duplicate date/type pairs.
        unique = {}

        for collection in collections:
            unique[
                (
                    collection.date,
                    collection.type,
                )
            ] = collection

        return sorted(
            unique.values(),
            key=lambda collection: (
                collection.date,
                collection.type,
            ),
        )