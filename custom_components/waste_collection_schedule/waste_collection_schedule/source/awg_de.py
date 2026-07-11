"""ZAW Donau-Wald / AWG (awg.de), Germany.

Demonstrates: an Athos "WasteManagementServlet" deployment that does NOT fit
``retrievers.AthosWasteManagementRetriever``. Three things are genuinely
irregular here and are replicated exactly as the legacy source did them:

* The servlet's TLS certificate fails verification, so every request must be
  sent with ``verify=False`` (the shared Athos retriever has no such escape
  hatch, and adding one for a single deployment would leak a security-relevant
  knob into every other Athos source).
* The servlet only accepts genuine ``multipart/form-data`` bodies (a
  hand-built ``------<boundary>`` payload with one part per field), not the
  urlencoded POST every other Athos deployment accepts.
* When the initial GET offers more than one ``Zeitraum`` (period) value (this
  provider publishes separate current/next-year calendars under one address),
  the whole CITYCHANGED -> forward -> filedownload_ICAL wizard must be re-run
  once per period and the results merged, rather than once per address.

None of the three is expressible with the shared retriever, so this source
keeps its own ``retrieve`` implementing the exact wire format instead.
"""

import html
import random
import re
import string
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, PAPER

_API_URL = (
    "https://wastemanagement.awg.de/WasteManagementDonauwald/WasteManagementServlet"
)

_INPUT_RE = re.compile('<INPUT\\sNAME="([^"]+?)"\\sID="[^"]+?"(?:\\sVALUE="([^"]*?)")?')
_ZEITRAUM_RE = re.compile('NAME="Zeitraum" VALUE="([^"]+?)"')


def _boundary() -> str:
    return "WebKitFormBoundary" + "".join(
        random.sample(string.ascii_letters + string.digits, 16)
    )


def _multipart_body(data: dict, boundary: str) -> bytes:
    result = ""
    for key, value in data.items():
        result += (
            f"------{boundary}\r\nContent-Disposition: form-data; "
            f'name="{key}"\r\n\r\n{value}\r\n'
        )
    result += f"------{boundary}--\r\n"
    return result.encode()


def _parse_hidden_inputs(text: str) -> dict:
    return dict(_INPUT_RE.findall(text))


@final
class Source(BaseSource):
    TITLE = "ZAW Donau-Wald"
    DESCRIPTION = "Source for ZAW Donau-Wald."
    URL = "https://www.awg.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Achslach Aign 1 ": {"city": "Achslach", "street": "Aign", "hnr": "1"},
        "Böbrach Bärnerauweg 10A": {
            "city": "Böbrach",
            "street": "Bärnerauweg",
            "hnr": 10,
            "addition": "A",
        },
        "Am Bäckergütl 1, 94094 Malching": {
            "city": "Malching",
            "street": "Am Bäckergütl",
            "hnr": 1,
            "addition": "",
        },
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
        house_number(field="hnr"),
        text_field("addition", "Address addition", optional=True),
    )

    transform = ICSTransformer(
        type_value_map={
            "Restmuelltonne": GENERAL_WASTE,
            "Restmüllcontainer": GENERAL_WASTE,
            "Papiercontainer": PAPER,
        }
    )

    def __init__(
        self,
        city: str,
        street: str,
        hnr: "str | int",
        addition: str = "",
    ):
        super().__init__(city=city, street=street, hnr=hnr, addition=addition)

    def _address(self) -> dict:
        return {
            "Ort": self.params["city"],
            "Strasse": self.params["street"],
            "Hausnummer": self.params["hnr"],
            "Hausnummerzusatz": self.params["addition"],
        }

    def _post(self, session, boundary: str, payload: dict):
        return session.post(
            _API_URL,
            headers={"Content-Type": f"multipart/form-data; boundary=----{boundary}"},
            data=_multipart_body(payload, boundary),
            verify=False,
        )

    def _payload(
        self, boundary: str, last_request: str, action: str, period: str, **kwargs
    ) -> dict:
        payload = _parse_hidden_inputs(last_request)
        payload.update({"SubmitAction": action, **kwargs})
        if period:
            payload.update({"Zeitraum": html.unescape(period)})
        return payload

    def _get_dates_for_period(
        self, session, boundary: str, init_request: str, calendar: str = ""
    ):
        city_response = self._post(
            session,
            boundary,
            self._payload(
                boundary,
                init_request,
                action="CITYCHANGED",
                period=calendar,
                Ort=self.params["city"],
                Strasse="",
            ),
        )
        final_response = self._post(
            session,
            boundary,
            self._payload(
                boundary,
                city_response.text,
                action="forward",
                period=calendar,
                **self._address(),
            ),
        )
        return self._post(
            session,
            boundary,
            self._payload(
                boundary,
                final_response.text,
                action="filedownload_ICAL",
                period=calendar,
                **self._address(),
            ),
        )

    def retrieve(self, source):
        session = self.session
        boundary = _boundary()

        init_request = session.get(
            f"{_API_URL}?SubmitAction=wasteDisposalServices&InFrameMode=true",
            verify=False,
        ).text

        calendars = _ZEITRAUM_RE.findall(init_request)
        if calendars:
            return [
                self._get_dates_for_period(session, boundary, init_request, calendar)
                for calendar in calendars
            ]
        return [self._get_dates_for_period(session, boundary, init_request)]

    def parse(self, response, source=None):
        from waste_collection_schedule.service.ICS import ICS

        entries: list = []
        for r in response:
            entries.extend(ICS().convert(r.text))
        return entries
