import html
import re
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "bonnorange AöR"
DESCRIPTION = (
    "Source for bonnorange AöR, the waste management company of Bonn, Germany."
)
URL = "https://www.bonnorange.de"
COUNTRY = "de"
TEST_CASES = {
    "Altes Rathaus, Markt 1": {"street": "Markt", "house_number": 1},
    "Stadthaus, Berliner Platz 2": {"street": "Berliner Platz", "house_number": 2},
    "Münsterplatz 1": {
        "street": "Münsterplatz",
        "house_number": 1,
        "address_suffix": "",
    },
}

ICON_MAP = {
    "Restabfallbehaelter": Icons.GENERAL_WASTE,
    "Bioabfallbehaelter": Icons.BIO_KITCHEN,
    "Papierbehaelter": Icons.PAPER,
    "Gelbe Behaelter": Icons.PLASTIC_PACKAGING,
    "Gelbe Grossbehaelter": Icons.PLASTIC_PACKAGING,
    "Sperrmuell": Icons.BULKY,
    "Weihnachtsbaeume": Icons.CHRISTMAS_TREE,
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
        "address_suffix": "Hausnummerzusatz",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Look up your address at https://www5.bonn.de/WasteManagementBonnOrange/WasteManagementServlet?SubmitAction=wasteDisposalServices and use the street name exactly as it is spelled in the drop-down list.",
    "de": "Adresse unter https://www5.bonn.de/WasteManagementBonnOrange/WasteManagementServlet?SubmitAction=wasteDisposalServices nachschlagen und den Straßennamen genau so angeben, wie er in der Auswahlliste steht.",
}

SERVLET = "https://www5.bonn.de/WasteManagementBonnOrange/WasteManagementServlet"

# Part of the form is delivered as a JavaScript string instead of plain markup.
TEXT_REGEX = re.compile(r"var\s*text\s*=\s*'(.*?)'\s*;", re.DOTALL)
OPTION_REGEX = re.compile(r'<OPTION VALUE="([^"]+)"', re.IGNORECASE)


class HiddenInputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._args: dict[str, str] = {}

    @property
    def args(self) -> dict[str, str]:
        return self._args

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if str(d.get("type", "")).lower() == "hidden":
                self._args[d["name"]] = d.get("value", "")


def _hidden_args(text: str) -> dict[str, str]:
    parser = HiddenInputParser()
    parser.feed(text)
    match = TEXT_REGEX.search(text)
    if match:
        parser.feed(match.group(1).encode().decode("unicode-escape"))
    return parser.args


def _streets(text: str) -> list[str]:
    # The drop-down separates street name and type with a non-breaking space.
    return [
        html.unescape(o).replace("\xa0", " ") for o in OPTION_REGEX.findall(text) if o
    ]


class Source:
    def __init__(self, street: str, house_number: int, address_suffix: str = ""):
        self._street: str = street
        self._house_number: int = house_number
        self._address_suffix: str = address_suffix
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        r = session.get(SERVLET, params={"SubmitAction": "wasteDisposalServices"})
        r.raise_for_status()
        r.encoding = "utf-8"

        args = _hidden_args(r.text)
        args["Ort"] = self._street[0]
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._house_number)
        args["Hausnummerzusatz"] = self._address_suffix
        args["SubmitAction"] = "CITYCHANGED"
        for i in range(1, 6):
            args[f"ContainerGewaehlt_{i}"] = "on"

        r = session.post(SERVLET, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        streets = _streets(r.text)
        if streets and self._street not in streets:
            raise SourceArgumentNotFoundWithSuggestions("street", self._street, streets)

        # Every step hands out fresh session tokens, so the hidden fields have to
        # be picked up again from each response.
        args.update(_hidden_args(r.text))
        args["SubmitAction"] = "forward"
        r = session.post(SERVLET, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        # The result page switches ApplicationName to the collection-date model,
        # which the iCal download depends on.
        args.update(_hidden_args(r.text))
        args["SubmitAction"] = "filedownload_ICAL"
        args["ICalErinnerung"] = "keine Erinnerung"
        args["ICalZeit"] = "18:00 Uhr"
        r = session.post(SERVLET, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        if "BEGIN:VCALENDAR" not in r.text:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, []
            )

        entries = []
        for d in self._ics.convert(r.text):
            bin_type = d[1].strip()
            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))
        return entries
