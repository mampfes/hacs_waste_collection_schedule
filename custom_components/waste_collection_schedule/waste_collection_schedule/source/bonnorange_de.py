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


class SelectOptionParser(HTMLParser):
    """Collects the options of one named drop-down.

    The page contains several selects (e.g. the first-letter chooser), so
    grabbing every option would mix unrelated values into the suggestions.
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name
        self._options: list[str] = []
        self._in_select = False

    @property
    def options(self) -> list[str]:
        return self._options

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "select":
            self._in_select = d.get("name") == self._name
        elif tag == "option" and self._in_select and d.get("value"):
            # Values carry non-breaking spaces: street name and type, number ranges.
            self._options.append(html.unescape(d["value"]).replace("\xa0", " "))

    def handle_endtag(self, tag):
        if tag == "select":
            self._in_select = False


def _options(text: str, name: str) -> list[str]:
    parser = SelectOptionParser(name)
    parser.feed(text)
    return parser.options


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

        streets = _options(r.text, "Strasse")
        if streets and self._street not in streets:
            raise SourceArgumentNotFoundWithSuggestions("street", self._street, streets)

        # Every step hands out fresh session tokens, so the hidden fields have to
        # be picked up again from each response.
        args.update(_hidden_args(r.text))
        args["SubmitAction"] = "forward"
        r = session.post(SERVLET, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        # An address the portal does not serve comes back with a drop-down of
        # the house numbers that are actually registered for this street.
        house_numbers = _options(r.text, "Hausnummernwahl")
        if house_numbers:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, house_numbers
            )

        # The result page switches ApplicationName to the collection-date model,
        # which the iCal download depends on.
        args.update(_hidden_args(r.text))
        args["SubmitAction"] = "filedownload_ICAL"
        args["ICalErinnerung"] = "keine Erinnerung"
        args["ICalZeit"] = "18:00 Uhr"
        r = session.post(SERVLET, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        if not r.text.lstrip().startswith("BEGIN:VCALENDAR"):
            raise ValueError(
                "Expected an iCalendar file from the bonnorange portal but got "
                f"{r.headers.get('Content-Type', 'an unknown content type')}, "
                "the portal may be unavailable or may have changed."
            )

        entries = []
        for d in self._ics.convert(r.text):
            bin_type = d[1].strip()
            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))
        return entries
