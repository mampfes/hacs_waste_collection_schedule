import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ICS import ICS

TITLE = "De Afvalapp"
DESCRIPTION = (
    "Source for De Afvalapp, used by several Dutch municipalities "
    "(e.g. Helmond, Land van Cuijk, Boekel, Maashorst)."
)
URL = "https://www.deafvalapp.nl"
COUNTRY = "nl"
EXTRA_INFO = [
    {"title": "Helmond", "url": "https://www.deafvalapp.nl"},
    {"title": "Land van Cuijk", "url": "https://www.deafvalapp.nl"},
    {"title": "Boekel", "url": "https://www.deafvalapp.nl"},
    {"title": "Maashorst", "url": "https://www.deafvalapp.nl"},
]
TEST_CASES = {
    "Maashorst": {"postcode": "5406XP", "house_number": "9"},
    "Helmond": {"postcode": "5701NC", "house_number": 1},
}

ICON_MAP = {
    "Rest": Icons.GENERAL_WASTE,
    "Restafval": Icons.GENERAL_WASTE,
    "Gft+e": Icons.BIO_KITCHEN,
    "GFT": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "PBD": Icons.PLASTIC_PACKAGING,
    "PMD": Icons.PLASTIC_PACKAGING,
    "KCA": Icons.HAZARDOUS,
    "Kringloop": Icons.RECYCLING,
    "Milieustraat": Icons.RECYCLING,
    "Mobiele Milieustraat": Icons.RECYCLING,
    "Repair Café": Icons.EVENT,
    "Compost": Icons.GARDEN,
    "Snoeiafval": Icons.GARDEN,
    "Keukenemmer": Icons.BIO_KITCHEN,
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the same postcode, house number and (optional) house number addition that you would use at https://www.deafvalapp.nl to look up your waste collection calendar.",
    "de": "Geben Sie dieselbe Postleitzahl, Hausnummer und (optional) den Hausnummernzusatz ein, die Sie auch unter https://www.deafvalapp.nl verwenden würden, um Ihren Abfallkalender abzurufen.",
    "fr": "Saisissez le même code postal, numéro de maison et (facultatif) complément de numéro que vous utiliseriez sur https://www.deafvalapp.nl pour consulter votre calendrier de collecte des déchets.",
    "it": "Inserisci lo stesso CAP, numero civico e (facoltativo) estensione del numero civico che utilizzeresti su https://www.deafvalapp.nl per consultare il tuo calendario di raccolta rifiuti.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postal code",
        "house_number": "House number",
        "house_number_addition": "House number addition",
    },
    "de": {
        "postcode": "Postleitzahl",
        "house_number": "Hausnummer",
        "house_number_addition": "Hausnummernzusatz",
    },
    "fr": {
        "postcode": "Code postal",
        "house_number": "Numéro de maison",
        "house_number_addition": "Complément de numéro",
    },
    "it": {
        "postcode": "CAP",
        "house_number": "Numero civico",
        "house_number_addition": "Estensione del numero civico",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Dutch postal code of your address, e.g. '5406XP'",
        "house_number": "House number of your address, e.g. '9'",
        "house_number_addition": "Optional house number addition, e.g. 'A'",
    },
    "de": {
        "postcode": "Niederländische Postleitzahl Ihrer Adresse, z. B. '5406XP'",
        "house_number": "Hausnummer Ihrer Adresse, z. B. '9'",
        "house_number_addition": "Optionaler Hausnummernzusatz, z. B. 'A'",
    },
    "fr": {
        "postcode": "Code postal néerlandais de votre adresse, par exemple '5406XP'",
        "house_number": "Numéro de maison de votre adresse, par exemple '9'",
        "house_number_addition": "Complément de numéro facultatif, par exemple 'A'",
    },
    "it": {
        "postcode": "CAP olandese del tuo indirizzo, ad es. '5406XP'",
        "house_number": "Numero civico del tuo indirizzo, ad es. '9'",
        "house_number_addition": "Estensione facoltativa del numero civico, ad es. 'A'",
    },
}

# ### End of arguments affecting the configuration GUI ####


SESSION_URL = "https://www.deafvalapp.nl/calendar/kalender_sessie.jsp"
ICS_URL = "https://www.deafvalapp.nl/calendar/afvalkalender.ics"


class Source:
    def __init__(
        self, postcode: str, house_number: str | int, house_number_addition: str = ""
    ):
        self._postcode = str(postcode).replace(" ", "").upper()
        self._house_number = str(house_number).strip()
        self._house_number_addition = (
            str(house_number_addition).strip() if house_number_addition else ""
        )
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # This first request creates a server-side session tied to the
        # provided address. The site always answers with a redirect,
        # regardless of whether the address is valid.
        session.get(
            SESSION_URL,
            params={
                "land": "NL",
                "postcode": self._postcode,
                "huisnr": self._house_number,
                "huisnrtoev": self._house_number_addition,
            },
            timeout=30,
        )

        r = session.get(ICS_URL, timeout=30)
        if r.status_code != 200:
            # The site returns a HTTP 500 ("sessie ongeldig") when the
            # postcode/house number combination could not be resolved.
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "please check the postcode and house number and try again.",
            )
        r.encoding = "utf-8"

        dates = self._ics.convert(r.text)
        if not dates:
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "no collections were found for this address, please check the postcode and house number.",
            )

        entries: list[Collection] = []
        for d in dates:
            entries.append(Collection(d[0], d[1], icon=ICON_MAP.get(d[1])))
        return entries
