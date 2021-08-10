from datetime import date
import re
import requests
from html.parser import HTMLParser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Generates request data payload to be sent as 'form-data'

TITLE = "RH Entsorgung"
DESCRIPTION = "Source for RHE (Rhein Hunsrück Entsorgung)."
URL = "https://www.rh-entsorgung.de"
TEST_CASES = {
    "Horn": {
        "city": "Horn",
        "street": "Hauptstraße",
        "house_number": 1
    },
    "Bärenbach": {
        "city": "Bärenbach",
        "street": "Schwarzener Straße",
        "house_number": 10
    }
}


def to_multipart_form_data(args: dict[str, str]) -> dict[str, (None, str)]:
    form_data_dict: dict[str, (None, str)] = {}
    for key, value in args.items():
        form_data_dict[key] = (None, value)
    return form_data_dict

# Parser for HTML input (hidden) text


class HiddenInputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._args = {}

    @property
    def args(self):
        return self._args

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if str(d["type"]).lower() == "hidden":
                self._args[d["name"]] = d["value"] if "value" in d else ""


class CollectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._entries: list[Collection] = []
        self._current_type: str = None
        self._capture_type: bool = False
        self._capture_date: bool = False
        self._date_pattern = re.compile(
            r'(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})')

    @property
    def entries(self):
        return self._entries

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "p":
            d = dict(attrs)
            if(str(d["class"]).lower() == "work"):
                self._capture_type = True
        if self._current_type != None and tag == "td":
            d = dict(attrs)
            if("class" in d) and ("dia_c_abfuhrdatum" in str(d["class"])):
                self._capture_date = True

    def handle_data(self, data: str) -> None:
        if self._capture_type:
            self._current_type = data
        if self._capture_date:
            match = self._date_pattern.match(data)
            self._entries.append(
                Collection(
                    date(int(match.group(3)), int(match.group(2)), int(match.group(1))),
                    self._current_type
                )
            )

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._capture_type:
            self._capture_type = False
        if tag == "td" and self._capture_date:
            self._capture_date = False


class Source:
    def __init__(self,
                 city: str,
                 street: str,
                 house_number: int,
                 address_suffix: str = "",
                 garbage_types: list[int] = [1, 2, 3, 4, 5]):
        self._city = city
        self._street = street
        self._hnr = house_number
        self._suffix = address_suffix
        self._garbage_types = garbage_types

    def append_custom_args(self, args, submit_action: str = None):
        args["Ort"] = self._city
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._hnr)
        args["Hausnummerzusatz"] = self._suffix
        args["Zeitraum"] = "Die Leerungen der nächsten 3 Monate"

        if submit_action != None:
            args["SubmitAction"] = submit_action

        for type in range(1, 6):
            args["ContainerGewaehlt_{}".format(
                type)] = "on" if type in self._garbage_types else "off"

        return args

    def fetch(self):
        parser = HiddenInputParser()
        r = requests.post(
            "https://aao.rh-entsorgung.de/WasteManagementRheinhunsrueck/WasteManagementServlet?SubmitAction=wasteDisposalServices&InFrameMode=TRUE")
        r.encoding = "utf-8"

        parser.feed(r.text)
        args = to_multipart_form_data(
            self.append_custom_args(parser.args, 'forward'))

        # First request returns wrong city. has to be called twice!
        r = requests.post(
            "https://aao.rh-entsorgung.de/WasteManagementRheinhunsrueck/WasteManagementServlet?SubmitAction=wasteDisposalServices&InFrameMode=TRUE",
            files=args,
            cookies=r.cookies,
            headers={
                'Cache-Control': 'no-cache'
            })

        r = requests.post(
            "https://aao.rh-entsorgung.de/WasteManagementRheinhunsrueck/WasteManagementServlet?SubmitAction=wasteDisposalServices&InFrameMode=TRUE",
            files=args,
            cookies=r.cookies,
            headers={
                'Cache-Control': 'no-cache'
            })
        r.encoding = "utf-8"

        date_parser = CollectionParser()
        date_parser.feed(r.text)
        return date_parser.entries
