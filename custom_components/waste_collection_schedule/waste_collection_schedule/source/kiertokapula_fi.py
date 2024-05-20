import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Kiertokapula Finland"
DESCRIPTION = "Schedule for kiertokapula FI"
URL = "https://www.kiertokapula.fi"
TEST_CASES = {
    "Test1": {
        "bill_number": "!secret kiertonkapula_fi_bill_number",
        "password": "!secret kiertonkapula_fi_bill_password",
    }
}
ICON_MAP = {
    "SEK": "mdi:trash-can",
    "MUO": "mdi:delete-variant",
    "KAR": "mdi:package-variant",
    "LAS": "mdi:glass-wine",
    "MET": "mdi:tools",
    "BIO": "mdi:leaf",
}
NAME_DEF = {
    "SEK": "Sekajäte",
    "MUO": "Muovi",
    "KAR": "Kartonki",
    "LAS": "Lasi",
    "MET": "Metalli",
    "BIO": "Bio",
}
API_URL = "https://asiakasnetti.kiertokapula.fi/kiertokapula"

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        bill_number,
        password,
    ):
        self._bill_number = bill_number
        self._password = password

    def fetch(self):
        session = requests.Session()
        session.headers.update({"X-Requested-With": "XMLHttpRequest"})
        session.get(API_URL)

        # sign in
        r = session.post(
            API_URL + "/j_acegi_security_check?target=2",
            data={
                "j_username": self._bill_number,
                "j_password": self._password,
                "remember-me": "false",
            },
        )
        r.raise_for_status()

        # get customer info

        r = session.get(API_URL + "/secure/get_customer_datas.do")
        r.raise_for_status()
        data = r.json()

        entries = []

        for estate in data.values():
            for customer in estate:
                r = session.get(
                    API_URL + "/secure/get_services_by_customer_numbers.do",
                    params={"customerNumbers[]": customer["asiakasnro"]},
                )
                r.raise_for_status()
                data = r.json()
                for service in data:
                    if service["tariff"].get("productgroup", "PER") == "PER":
                        continue
                    next_date_str = None
                    if (
                        "ASTSeurTyhj" in service
                        and service["ASTSeurTyhj"] is not None
                        and len(service["ASTSeurTyhj"]) > 0
                    ):
                        next_date_str = service["ASTSeurTyhj"]
                    elif (
                        "ASTNextDate" in service
                        and service["ASTNextDate"] is not None
                        and len(service["ASTNextDate"]) > 0
                    ):
                        next_date_str = service["ASTNextDate"]

                    if next_date_str is None:
                        continue

                    next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
                    entries.append(
                        Collection(
                            date=next_date,
                            t=service.get(
                                "ASTNimi",
                                NAME_DEF.get(service["tariff"]["productgroup"], "N/A"),
                            ),
                            icon=ICON_MAP.get(service["tariff"]["productgroup"]),
                        )
                    )

        return entries
