import binascii
import json
from datetime import date, datetime
from typing import Any, Literal, NotRequired, TypedDict

import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound


class Municipality(TypedDict):
    PAYLOAD: dict[str, str | int]
    API_URL: str
    title: str
    url: str
    # Councils which have retired the kmbd/collectionDay API are looked up
    # through the "My Council Services" portal instead. PORTAL_CUID is the
    # customer UID of the bin collection form, taken from the link the council
    # website points at. See _fetch_portal() below.
    PORTAL_CUID: NotRequired[str]


TITLE = "iTouchVision Source using the encrypted API"
DESCRIPTION = "Source for iTouchVision Source using the encrypted API."
URL = "https://www.itouchvision.com/"
TEST_CASES = {
    "Buckinghamshire: 100080550517": {
        "uprn": 100080550517,
        "municipality": "BUCKINGHAMSHIRE",
    },
    "newport: 10090955364": {"uprn": "10090955364", "municipality": "NEWPORT"},
    "blaenau gwent: 100100457787": {
        "uprn": "100100457787",
        "municipality": "BLAENAU GWENT",
    },
    "Winchester: 10090844134": {"uprn": "10090844134", "municipality": "WINCHESTER"},
    "Aylesbury Vale: 766251559": {
        "uprn": 766251559,
        "municipality": "AYLESBURY VALE",
    },
    "Somerset (including former merged councils)": {
        "uprn": 30071272,
        "municipality": "SOMERSET",
    },
    "Test Valley": {"uprn": 100060571645, "municipality": "TEST VALLEY"},
    "Hyndburn": {"uprn": 100010439798, "municipality": "HYNDBURN"},
    "Epsom and Ewell: 100061354185": {
        "uprn": "100061354185",
        "municipality": "EPSOM AND EWELL",
    },
}
COUNTRY = "uk"
ICON_MAP = {
    "Food waste": Icons.BIO_KITCHEN,
    "Food Waste": Icons.BIO_KITCHEN,
    "FOOD WASTE": Icons.BIO_KITCHEN,
    "General waste": Icons.GENERAL_WASTE,
    "Mixed recycling": Icons.RECYCLING,
    "Paper and cardboard": Icons.PAPER,
    "Paper and cardboard recycling": Icons.PAPER,
    "Textiles/Batteries/Electricals": Icons.BATTERY,
    "Small household electricals, batteries and textiles": Icons.BATTERY,
    "GARDEN WASTE": Icons.GARDEN,
    "Garden waste": Icons.GARDEN,
    "HOUSEHOLD WASTE": Icons.GENERAL_WASTE,
    "RECYCLING": Icons.RECYCLING,
    "Recycling collection": Icons.RECYCLING,
    "Refuse Bin": Icons.GENERAL_WASTE,
    "Garden Waste Collection": Icons.GARDEN,
    "General Waste Collection": Icons.GENERAL_WASTE,
    "Glass Collection": Icons.GLASS,
    "Recycling Collection": Icons.RECYCLING,
    "Garden": Icons.GARDEN,
    "Recycling": Icons.RECYCLING,
    "Rubbish": Icons.GENERAL_WASTE,
    "Garden Waste": Icons.GARDEN,
    "Household Waste": Icons.GENERAL_WASTE,
    "RECYCLING - BLUE": Icons.RECYCLING,
    "RECYCLING - BROWN": Icons.NEWSPAPER,
    "RECYCLING - GREEN": Icons.ORGANIC,
    "REFUSE": Icons.GENERAL_WASTE,
    "Green Garden Waste": Icons.GARDEN,
    "Recycling and Food": Icons.RECYCLING,
    "Refuse and Glass": Icons.GENERAL_WASTE,
}

# Global variables for encryption key and IV
KEY = binascii.unhexlify(
    "F57E76482EE3DC3336495DEDEEF3962671B054FE353E815145E29C5689F72FEC"
)
IV = binascii.unhexlify("2CBF4FC35C69B82362D393A4F0B9971A")

# Base URL of the "My Council Services" portal API, used by the PORTAL_CUID
# municipalities. It shares the encryption scheme with the collectionDay API.
PORTAL_API_URL = "https://itouchvision.app/portal/itouchvision/"

# Customer UID of the Buckinghamshire "Check your next bin collection date"
# form, as linked from
# https://www.buckinghamshire.gov.uk/waste-and-recycling/bin-collections/find-out-when-its-your-bin-collection/
BUCKINGHAMSHIRE_PORTAL_CUID = "1620D584419C7043A8323332E0634D00A8C0D5EF"

# The portal renders dates as "Monday 7 September", without a year. Month and
# weekday names are matched explicitly because strptime()/strftime() would
# resolve them against the running system's locale.
WEEKDAY_NAMES = {
    name: number
    for number, name in enumerate(
        (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        )
    )
}
MONTH_NAMES = {
    name: number
    for number, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}


# Encryption function
def encrypt_aes(plaintext: str) -> str:
    data = plaintext.encode("utf-8")
    padded_data = pad(data, AES.block_size)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ciphertext = cipher.encrypt(padded_data)
    return binascii.hexlify(ciphertext).decode("utf-8")


# Decryption function
def decrypt_aes(ciphertext_hex: str) -> str:
    ciphertext = binascii.unhexlify(ciphertext_hex)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted_data = cipher.decrypt(ciphertext)
    plaintext = unpad(decrypted_data, AES.block_size).decode("utf-8")
    return plaintext


def resolve_collection_date(text: str, today: date) -> date:
    """Turn a portal date such as "Monday 7 September" into a real date.

    The year is missing from the response, so the candidate years around today
    are checked against the weekday name and the closest match is taken. That
    keeps collections just after New Year in the right year.
    """
    weekday_name, day, month_name = text.split()

    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidate = date(year, MONTH_NAMES[month_name], int(day))
        except (KeyError, ValueError):
            continue
        if candidate.weekday() == WEEKDAY_NAMES.get(weekday_name, candidate.weekday()):
            candidates.append(candidate)

    if not candidates:
        raise ValueError(f"Unexpected collection date: {text}")
    return min(candidates, key=lambda candidate: abs(candidate - today))


MUNICIPALITIES: dict[str, Municipality] = {
    "BUCKINGHAMSHIRE": {
        "PAYLOAD": {
            "P_CLIENT_ID": 152,
            "P_COUNCIL_ID": 34505,
        },
        "API_URL": "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay",
        "PORTAL_CUID": BUCKINGHAMSHIRE_PORTAL_CUID,
        "title": "Buckinghamshire: Formerly (Chiltern, South Bucks, Wycombe)",
        "url": "https://www.buckinghamshire.gov.uk/",
    },
    "NEWPORT": {
        "PAYLOAD": {
            "P_CLIENT_ID": 130,
            "P_COUNCIL_ID": 260,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Newport City Council",
        "url": "https://www.newport.gov.uk/",
    },
    "BLAENAU GWENT": {
        "PAYLOAD": {
            "P_CLIENT_ID": 106,
            "P_COUNCIL_ID": 35,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Blaenau Gwent County Borough Council",
        "url": "https://www.blaenau-gwent.gov.uk/",
    },
    "WINCHESTER": {
        "PAYLOAD": {
            "P_CLIENT_ID": 43,
            "P_COUNCIL_ID": 433,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Winchester City Council",
        "url": "https://www.winchester.gov.uk",
    },
    "AYLESBURY VALE": {
        "PAYLOAD": {
            "P_CLIENT_ID": 152,
            "P_COUNCIL_ID": 34505,
        },
        "API_URL": "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay",
        "PORTAL_CUID": BUCKINGHAMSHIRE_PORTAL_CUID,
        "title": "Aylesbury Vale District Council",
        "url": "https://www.aylesburyvaledc.gov.uk/",
    },
    "SOMERSET": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Somerset Council",
        "url": "https://www.somerset.gov.uk/",
    },
    "SOUTH SOMERSET": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "South Somerset District Council",
        "url": "https://www.southsomerset.gov.uk/",
    },
    "MENDIP": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Mendip District Council",
        "url": "https://www.mendip.gov.uk/",
    },
    "SEDGEMOOR": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Sedgemoor District Council",
        "url": "https://www.sedgemoor.gov.uk",
    },
    "SOMERSET WEST AND TAUNTON": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Somerset West & Taunton District Council",
        "url": "https://www.somersetwestandtaunton.gov.uk/",
    },
    "SOMERSET COUNTY": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Somerset County Council",
        "url": "https://www.somerset.gov.uk/",
    },
    "TEST VALLEY": {
        "PAYLOAD": {
            "P_CLIENT_ID": 94,
            "P_COUNCIL_ID": 390,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Test Valley Borough Council",
        "url": "https://www.testvalley.gov.uk/",
    },
    "HYNDBURN": {
        "PAYLOAD": {
            "P_CLIENT_ID": 157,
            "P_COUNCIL_ID": 34508,
        },
        # "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "API_URL": "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay",
        "title": "Hyndburn Borough Council",
        "url": "https://www.hyndburnbc.gov.uk/",
    },
    "EPSOM AND EWELL": {
        "PAYLOAD": {
            "P_CLIENT_ID": 138,
            "P_COUNCIL_ID": 140,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Epsom and Ewell Borough Council",
        "url": "https://www.epsom-ewell.gov.uk/",
    },
}

MUNICIPALITY_LITERALS = Literal[
    "BUCKINGHAMSHIRE",
    "NEWPORT",
    "BLAENAU GWENT",
    "WINCHESTER",
    "AYLESBURY VALE",
    "SOMERSET",
    "SOUTH SOMERSET",
    "MENDIP",
    "SEDGEMOOR",
    "SOMERSET WEST AND TAUNTON",
    "SOMERSET COUNTY",
    "TEST VALLEY",
    "HYNDBURN",
    "EPSOM AND EWELL",
]

EXTRA_INFO = [
    {
        "title": m["title"],
        "url": m["url"],
        "country": COUNTRY,
        "default_params": {"municipality": key},
    }
    for key, m in MUNICIPALITIES.items()
]


class PortalForm(TypedDict):
    """Portal identifiers discovered at runtime, see Source._discover_portal_form()."""

    BASE_PAYLOAD: dict[str, Any]
    ITEM_ID: int
    WS_ID: int
    INPUT_LABEL: str
    REPORT_ID: int


class Source:
    def __init__(self, uprn: str | int, municipality: MUNICIPALITY_LITERALS):
        self._uprn: str | int = uprn
        if municipality.upper() not in MUNICIPALITIES:
            raise ValueError(f"Unknown municipality: {municipality}")
        self._payload = MUNICIPALITIES[municipality.upper()]["PAYLOAD"]
        self._api_url = MUNICIPALITIES[municipality.upper()]["API_URL"]
        self._portal_cuid = MUNICIPALITIES[municipality.upper()].get("PORTAL_CUID")
        self._portal_form: PortalForm | None = None

    def fetch(self) -> list[Collection]:
        if self._portal_cuid:
            return self._fetch_portal()
        return self._fetch_collection_day()

    def _fetch_collection_day(self) -> list[Collection]:
        session = requests.Session()

        # Prepare the data to be encrypted
        payload: dict[str, str | int] = {
            "P_UPRN": self._uprn,
            **self._payload,
            "P_LANG_CODE": "EN",
        }

        # Encrypt the payload
        encrypted_payload = encrypt_aes(json.dumps(payload))

        # Send the request with the encrypted data
        response = session.get(
            self._api_url,
            headers={
                "P_PARAMETER": encrypted_payload,
            },
        )
        response.raise_for_status()

        # Decrypt the response
        decrypted_response = decrypt_aes(response.text)

        # Parse the JSON response
        servicedata = json.loads(decrypted_response)

        # Process the collection dates
        entries = []
        for service in servicedata["collectionDay"]:
            collection_dates = [
                datetime.strptime(service["collectionDay"], "%d-%m-%Y").date()
            ]
            try:
                collection_dates.append(
                    datetime.strptime(service["followingDay"], "%d-%m-%Y").date()
                )
            except Exception:
                pass
            bin_type = service["binType"].split(" (")[0].split(":")[0]
            for collection_date in collection_dates:
                entries.append(
                    Collection(
                        date=collection_date, t=bin_type, icon=ICON_MAP.get(bin_type)
                    )
                )

        return entries

    def _fetch_portal(self) -> list[Collection]:
        """Fetch the collections from the "My Council Services" portal.

        The portal serves the schedule as a rendered HTML table from a web
        service attached to a form. The form is filled in by a citizen, so the
        web service is addressed by the id of a draft service request. That
        draft is created once and reused; if the portal ever discards it, the
        form identifiers are discovered again and the request is retried.
        """
        session = requests.Session()

        for _ in range(2):
            if self._portal_form is None:
                self._portal_form = self._discover_portal_form(session)

            output = self._request_collection_output(session, self._portal_form)
            if output is not None:
                return self._parse_collection_output(output)

            self._portal_form = None

        raise Exception("The portal did not return a collection schedule")

    def _discover_portal_form(self, session: requests.Session) -> PortalForm:
        """Look up the form identifiers the collection web service is called with."""
        category_link = self._portal_get(
            session,
            "gdsv5/service/getcategorylinkdata",
            {"P_CAT_UID": self._portal_cuid},
        )["CATEGORY_LINK"][0]

        client = self._portal_get(
            session,
            "gdsv5/util/igetclientdetails",
            {"P_UID": category_link["ITV_APEX_URL"], "P_LANGUAGE_CODE": "EN"},
        )
        base_payload: dict[str, Any] = {
            "P_CLIENT_ID": client["P_CLIENT_ID"],
            "P_ACCESS_KEY": client["P_ACCESS_KEY"],
            "LANG_CODE": "EN",
        }

        form = self._portal_get(
            session,
            "gdsv5/plugin/getformdata",
            {
                **base_payload,
                "P_CATEGORY_ID": category_link["CATEGORY_ID"],
                "P_REPORT_ID": "",
                "P_USER_ID": None,
            },
        )
        items = (
            item
            for page in form["PAGES"]
            for region in page.get("REGIONS", [])
            for item in region.get("ITEMS", [])
        )
        web_service = next(
            item for item in items if item.get("I_TYPE") == "WEB_SERVICE_REF"
        )

        mapping = self._portal_get(
            session,
            "gdsv5/plugin/getWSRInputMapping",
            {
                **base_payload,
                "P_ITEM_ID": web_service["I_ID"],
                "P_WS_ID": web_service["I_WS_ID"],
                "P_REPORT_ID": "",
                "P_USER_ID": None,
            },
        )

        report = self._portal_post(
            session,
            "gdsv5/service/saveqadata",
            {
                "P_ACCESS_KEY": client["P_ACCESS_KEY"],
                "P_APP_ID": 0,
                "P_REPORT_ID": None,
                "P_USER_ID": None,
                "P_CATEGORY_ID": category_link["CATEGORY_ID"],
                "P_CLIENT_ID": client["P_CLIENT_ID"],
                "P_COUNCIL_ID": client["P_COUNCIL_ID"],
                "P_FORM_ID": form["F_ID"],
                "P_LANGUAGE_CODE": "EN",
                "P_ALLOW_START_PAGE": 1,
                "P_SKIPPED_PAGE_ID": "",
                "P_PAGE_ID": form["PAGES"][0]["P_ID"],
                "P_REPORT_DATA": [],
            },
        )

        return PortalForm(
            BASE_PAYLOAD=base_payload,
            ITEM_ID=web_service["I_ID"],
            WS_ID=web_service["I_WS_ID"],
            INPUT_LABEL=mapping["WS_INPUTS"][0]["label"],
            REPORT_ID=report["P_REPORT_ID"],
        )

    def _request_collection_output(
        self, session: requests.Session, portal_form: PortalForm
    ) -> str | None:
        """Call the collection web service, None if the draft request went stale."""
        result = self._portal_get(
            session,
            "gdsv5/plugin/getWSRResult",
            {
                **portal_form["BASE_PAYLOAD"],
                "P_ITEM_ID": portal_form["ITEM_ID"],
                "P_WS_ID": portal_form["WS_ID"],
                "P_REPORT_ID": portal_form["REPORT_ID"],
                "P_INPUT_DATA": {portal_form["INPUT_LABEL"]: str(self._uprn)},
            },
        )["WSR_VALUE"]

        if "OUTPUT_DATA" not in result:
            return None
        return result["OUTPUT_DATA"][0]["VAL"]

    def _parse_collection_output(self, output: str) -> list[Collection]:
        soup = BeautifulSoup(output, "html.parser")
        rows = soup.select("table.govuk-table tbody tr")
        if not rows:
            # An unknown UPRN is answered with a plain message instead of a table.
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                soup.get_text(" ", strip=True)
                or "please check the spelling and try again.",
            )

        today = date.today()
        entries = []
        for row in rows:
            cells = row.select("td")
            bin_type = cells[1].get_text(strip=True)
            entries.append(
                Collection(
                    date=resolve_collection_date(cells[0].get_text(strip=True), today),
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries

    def _portal_get(
        self, session: requests.Session, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        response = session.get(
            PORTAL_API_URL + endpoint,
            headers={"P_PARAMETER": encrypt_aes(json.dumps(payload))},
        )
        response.raise_for_status()
        return json.loads(decrypt_aes(response.text))

    def _portal_post(
        self, session: requests.Session, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        response = session.post(
            PORTAL_API_URL + endpoint,
            data=encrypt_aes(json.dumps(payload)),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        response.raise_for_status()
        return json.loads(decrypt_aes(response.text))
