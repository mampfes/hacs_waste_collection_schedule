"""Source for Sunderland City Council bin collection information."""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

# ============================================================================
# WASTE COLLECTION SCHEDULE SOURCE METADATA
# ============================================================================

TITLE = "Sunderland City Council"

DESCRIPTION = "Source for Sunderland City Council bin collection schedules."

URL = "https://www.sunderland.gov.uk/bindays?ccp=true"

COUNTRY = "uk"

TEST_CASES = {
    "Test_001": {"postcode": "SR4 7PU", "address": "191 Cleveland Road"},
    "Test_002": {"postcode": "SR3 2DW", "address": "43 Hill Street"},
    "Test_003": {"postcode": "SR4 8RJ", "address": "17 Sutherland Drive"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "address": "Address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "The postcode for the property.",
        "address": "The full address of the property.",
    }
}


# ============================================================================
# SUNDERLAND / GOSS CONFIGURATION
# ============================================================================

BASE_URL = "https://www.sunderland.gov.uk"

BIN_DAYS_URL = f"{BASE_URL}/bindays?ccp=true"

FORM_PREFIX = "BINCOLLECTIONCHECKERNEWV3"

POSTCODE_FIELD = f"{FORM_PREFIX}_ADDRESSSEARCH_SCCPOSTCODE"

ADDRESS_FIELD = f"{FORM_PREFIX}_ADDRESSSEARCH_SCCLISTOFADDRESSES"

POSTCODE_TRIGGER = f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODETRIGGER"

FORM_ACTION_NEXT = f"{FORM_PREFIX}_FORMACTION_NEXT"

UPRN_FIELD = f"{FORM_PREFIX}_ADDRESSSEARCH_UPRN"

POSTCODE_RESULT_FIELD = f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODE"

ADDRESS_TEXT_FIELD = f"{FORM_PREFIX}_ADDRESSSEARCH_ADDRESSTEXT"

FORM_DATA_PATTERN = re.compile(r'BINCOLLECTIONCHECKERNEWV3FormData\s*=\s*"([^"]+)"')


class Source:
    """Sunderland City Council source."""

    def __init__(self, postcode: str, address: str):
        self._postcode = self._normalise_postcode(postcode)
        self._address = address

        self._session = requests.Session(impersonate="chrome")

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _normalise_postcode(
        postcode: str,
    ) -> str:
        """Normalise a UK postcode."""

        return re.sub(
            r"\s+",
            " ",
            str(postcode).strip().upper(),
        )

    @staticmethod
    def _follow_redirects(
        session,
        location: str,
    ):
        """
        Follow Sunderland/GOSS redirects manually.

        Sunderland uses a mixture of 303 and 302 redirects
        and the intermediate pages must retain the same
        session/cookies.
        """

        while True:
            response = session.get(
                location,
                allow_redirects=False,
                timeout=30,
            )

            if response.status_code not in (
                301,
                302,
                303,
                307,
                308,
            ):
                return response

            redirect = response.headers.get("Location")

            if not redirect:
                return response

            location = urljoin(
                response.url,
                redirect,
            )

    @staticmethod
    def _element_value(
        element,
    ) -> str:
        """Return the value of a form element."""

        if element.name == "textarea":
            return element.text or ""

        if element.name == "select":
            selected = element.find(
                "option",
                selected=True,
            )

            if selected:
                return selected.get(
                    "value",
                    "",
                )

            return ""

        return element.get(
            "value",
            "",
        )

    @classmethod
    def _build_form_data(
        cls,
        form,
        include_buttons: bool = False,
    ) -> dict[str, str]:
        """Build POST data from a GOSS form."""

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

            element_type = (element.get("type") or "").lower()

            # Buttons are only included when explicitly
            # requested. The postcode form needs its
            # NEXT button.
            if element.name == "button":
                if not include_buttons:
                    continue

                if name != FORM_ACTION_NEXT:
                    continue

            if element_type in (
                "submit",
                "button",
                "image",
            ):
                if not include_buttons:
                    continue

            if element_type in (
                "checkbox",
                "radio",
            ):
                if not element.has_attr("checked"):
                    continue

            data[name] = cls._element_value(element)

        return data

    # =========================================================================
    # STEP 1 - INITIAL PAGE
    # =========================================================================

    def _get_initial_page(self):
        """Open the Sunderland bin checker."""

        response = self._session.get(
            BIN_DAYS_URL,
            timeout=30,
        )

        response.raise_for_status()

        return response

    def _find_postcode_form(
        self,
        html: str,
    ):
        """Find the postcode search form."""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        postcode = soup.find(
            "input",
            {
                "name": POSTCODE_FIELD,
            },
        )

        if postcode is None:
            raise SourceArgumentNotFoundWithSuggestions("postcode", "", [])

        form = postcode.find_parent("form")

        if form is None:
            raise SourceArgumentNotFoundWithSuggestions("postcode", "", [])

        return form

    # =========================================================================
    # STEP 2 - POSTCODE LOOKUP
    # =========================================================================

    def _lookup_postcode(
        self,
    ):
        """Submit the postcode and retrieve addresses."""

        initial = self._get_initial_page()

        form = self._find_postcode_form(initial.text)

        action = form.get("action")

        if not action:
            raise SourceArgumentNotFoundWithSuggestions("postcode", self._postcode, [])

        process_url = urljoin(
            initial.url,
            action,
        )

        data = self._build_form_data(
            form,
            include_buttons=True,
        )

        # Exact postcode entered by the user.
        data[POSTCODE_FIELD] = self._postcode

        # Exact action used by the working
        # standalone Sunderland flow.
        data[FORM_ACTION_NEXT] = POSTCODE_TRIGGER

        response = self._session.post(
            process_url,
            data=data,
            allow_redirects=False,
            timeout=30,
        )

        response.raise_for_status()

        if response.status_code not in (
            301,
            302,
            303,
            307,
            308,
        ):
            raise SourceArgumentNotFoundWithSuggestions(
                "postcode",
                self._postcode,
                [],
            )

        location = response.headers.get("Location")

        if not location:
            raise SourceArgumentNotFoundWithSuggestions("postcode", self._postcode, [])

        location = urljoin(
            response.url,
            location,
        )

        return self._follow_redirects(
            self._session,
            location,
        )

    # =========================================================================
    # STEP 3 - ADDRESS LIST
    # =========================================================================

    @staticmethod
    def _get_addresses(
        html: str,
    ):
        """Extract addresses returned by Sunderland."""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        select = soup.find(
            "select",
            {
                "name": ADDRESS_FIELD,
            },
        )

        if select is None:
            return []

        addresses = []

        for option in select.find_all("option"):
            value = option.get(
                "value",
                "",
            ).strip()

            text = option.get_text(
                " ",
                strip=True,
            )

            if value:
                addresses.append(
                    (
                        value,
                        text,
                    )
                )

        return addresses

    # =========================================================================
    # STEP 4 - SUBMIT SELECTED ADDRESS
    # =========================================================================

    def _submit_address(
        self,
        html: str,
        uprn: str,
        address: str,
    ):
        """Submit the selected UPRN."""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        select = soup.find(
            "select",
            {
                "name": ADDRESS_FIELD,
            },
        )

        if select is None:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        form = select.find_parent("form")

        if form is None:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        action = form.get("action")

        if not action:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        process_url = urljoin(
            BASE_URL,
            action,
        )

        data = self._build_form_data(
            form,
            include_buttons=False,
        )

        # These exactly reproduce the Javascript
        # event handler from Sunderland:
        #
        # helper.setFieldValue(
        #     "POSTCODE",
        #     helper.getFieldValue("SCCPOSTCODE")
        # )
        #
        # helper.setFieldValue("UPRN", value)
        #
        # helper.setFieldValue(
        #     "ADDRESSTEXT",
        #     selected address
        # )
        #
        # helper.triggerActionButton("NEXT")

        data[ADDRESS_FIELD] = uprn

        data[POSTCODE_RESULT_FIELD] = self._postcode

        data[UPRN_FIELD] = uprn

        data[ADDRESS_TEXT_FIELD] = address

        data[FORM_ACTION_NEXT] = POSTCODE_TRIGGER

        response = self._session.post(
            process_url,
            data=data,
            allow_redirects=False,
            timeout=30,
        )

        response.raise_for_status()

        if response.status_code not in (
            301,
            302,
            303,
            307,
            308,
        ):
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [],
            )

        location = response.headers.get("Location")

        if not location:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        location = urljoin(
            response.url,
            location,
        )

        return self._follow_redirects(
            self._session,
            location,
        )

    # =========================================================================
    # STEP 5 - SERIALIZED FORM DATA
    # =========================================================================

    @staticmethod
    def _extract_form_data(
        html: str,
    ):
        """Extract BINCOLLECTIONCHECKERNEWV3FormData."""

        match = FORM_DATA_PATTERN.search(html)

        if not match:
            raise SourceArgumentNotFoundWithSuggestions("address", "", [])

        encoded = match.group(1)

        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as error:
            raise SourceArgumentNotFoundWithSuggestions("address", "", []) from error

        try:
            return json.loads(decoded)
        except json.JSONDecodeError as error:
            raise SourceArgumentNotFoundWithSuggestions("address", "", []) from error

    @staticmethod
    def _extract_result(
        form_data,
    ):
        """Extract result from DATARETURNED."""

        address_search = form_data.get(
            "ADDRESSSEARCH_1",
            {},
        )

        raw = address_search.get("DATARETURNED")

        if not raw:
            raise SourceArgumentNotFoundWithSuggestions("address", "", [])

        if isinstance(raw, dict):
            return raw.get(
                "result",
                raw,
            )

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as error:
            raise SourceArgumentNotFoundWithSuggestions("address", "", []) from error

        return decoded.get(
            "result",
            decoded,
        )

    # =========================================================================
    # STEP 6 - COLLECTION PARSING
    # =========================================================================

    @staticmethod
    def _parse_date(
        value,
    ):
        """Parse Sunderland's ISO date."""

        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(
                str(value).replace(
                    "Z",
                    "+00:00",
                )
            )

            # WCS requires datetime.date objects,
            # not datetime.datetime objects.
            return parsed.date()

        except ValueError:
            return None

    @classmethod
    def _create_collections(
        cls,
        result,
    ):
        """Convert Sunderland schedules into Collections."""

        collections = []

        schedules = result.get(
            "schedules",
            [],
        )

        for schedule in schedules:
            status = str(
                schedule.get(
                    "status",
                    "",
                )
            ).upper()

            # Sunderland can return PLANNED services
            # such as garden waste and bulky collections.
            #
            # Only IN SERVICE schedules represent actual
            # active household collection schedules.
            if status != "IN SERVICE":
                continue

            bin_name = (
                schedule.get("binName") or schedule.get("jobName") or "Bin Collection"
            )

            future_jobs = schedule.get(
                "futureJobs",
                [],
            )

            for date_value in future_jobs:
                date = cls._parse_date(date_value)

                if date is None:
                    continue

                collections.append(
                    Collection(
                        date,
                        bin_name,
                    )
                )

        return collections

    # =========================================================================
    # MAIN WCS ENTRY POINT
    # =========================================================================

    def fetch(self):
        """Fetch all available Sunderland collections."""

        if not self._postcode:
            raise SourceArgumentNotFoundWithSuggestions("postcode", self._postcode, [])

        # -------------------------------------------------------------
        # Postcode lookup
        # -------------------------------------------------------------

        address_page = self._lookup_postcode()

        addresses = self._get_addresses(address_page.text)

        if not addresses:
            raise SourceArgumentNotFoundWithSuggestions(
                "postcode",
                self._postcode,
                [],
            )

        # -------------------------------------------------------------
        # Address selection
        # -------------------------------------------------------------

        #
        requested_address = " ".join(str(self._address or "").split()).casefold()
        address_map = {
            " ".join(address_text.split()).casefold(): (uprn, address_text)
            for uprn, address_text in addresses
        }

        if requested_address not in address_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [address_text for _, address_text in addresses],
            )

        uprn, address = address_map[requested_address]

        # -------------------------------------------------------------
        # Address submission
        # -------------------------------------------------------------

        final_page = self._submit_address(
            address_page.text,
            uprn,
            address,
        )

        # -------------------------------------------------------------
        # Extract serialized GOSS data
        # -------------------------------------------------------------

        form_data = self._extract_form_data(final_page.text)

        # -------------------------------------------------------------
        # Extract API result
        # -------------------------------------------------------------

        result = self._extract_result(form_data)

        # -------------------------------------------------------------
        # Convert schedules into WCS collections
        # -------------------------------------------------------------

        collections = self._create_collections(result)

        # -------------------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------------------

        unique = {}

        for collection in collections:
            key = (
                collection.date,
                collection.type,
            )

            unique[key] = collection

        collections = list(unique.values())

        # -------------------------------------------------------------
        # Sort chronologically
        # -------------------------------------------------------------

        collections.sort(key=lambda collection: collection.date)

        return collections
