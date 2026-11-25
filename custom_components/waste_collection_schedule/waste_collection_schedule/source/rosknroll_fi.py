import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "RosknRoll Finland"
DESCRIPTION = "Schedule for RosknRoll FI"
URL = "https://www.rosknroll.fi"
TEST_CASES = {
    "Test1": {
        "bill_number": "!secret rosknroll_fi_bill_number",
        "password": "!secret rosknroll_fi_bill_password",
    }
}

API_URL = "https://oma.rosknroll.fi/api"
TENANT_ID = "f792f414-5c5b-47ef-9176-9c9031d18227"

# Mapping of Finnish waste type keywords in the contract name to
# (type name, icon). The keyword match is case-insensitive substring.
TYPE_MAP = {
    "sekajäte": ("Sekajäte", Icons.GENERAL_WASTE),
    "muovi": ("Muovi", Icons.GENERAL_WASTE),
    "kartonki": ("Kartonki", Icons.PAPER),
    "lasi": ("Lasi", Icons.GLASS_COLORED),
    "metalli": ("Metalli", Icons.METAL),
    "energiajäte": ("Energiajäte", Icons.COMBUSTIBLE),
    "biojäte": ("Biojäte", Icons.ORGANIC),
    "bio": ("Bio", Icons.ORGANIC),
}

# Contracts whose name contains any of these are a fixed monthly fee
# (perusmaksu) rather than an emptying and must be ignored.
FEE_KEYWORDS = ("perusmaksu",)

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        bill_number,
        password,
    ):
        self._bill_number = bill_number
        self._password = password

    def _login(self, session: requests.Session) -> str:
        r = session.post(
            API_URL + "/customers/Users/login",
            json={"userName": self._bill_number, "password": self._password},
            headers={
                "Tenant-Id": TENANT_ID,
                "Content-Type": "application/json;charset=utf-8",
            },
        )
        r.raise_for_status()
        token = r.json().get("token")
        if not token:
            raise RuntimeError("Login failed: no token returned")
        return token

    def fetch(self):
        session = requests.Session()
        token = self._login(session)
        session.headers.update({"Authorization": f"Vingo-e-services {token}"})

        r = session.get(API_URL + "/customers/Customers/emptying-infos")
        r.raise_for_status()
        customers = r.json()

        entries = []

        for customer in customers:
            customer_id = customer["id"]
            r = session.get(
                API_URL + f"/customers/Customers/emptying-infos/{customer_id}/contracts"
            )
            r.raise_for_status()

            for contract in r.json():
                next_emptying = contract.get("nextEmptying")
                if not next_emptying:
                    continue

                name = contract.get("name", "")
                name_lower = name.lower()
                if any(kw in name_lower for kw in FEE_KEYWORDS):
                    continue

                type_name, icon = None, None
                for keyword, (tn, ic) in TYPE_MAP.items():
                    if keyword in name_lower:
                        type_name, icon = tn, ic
                        break
                if type_name is None:
                    type_name = name

                date = datetime.strptime(next_emptying[:10], "%Y-%m-%d").date()
                entries.append(Collection(date=date, t=type_name, icon=icon))

        return entries
