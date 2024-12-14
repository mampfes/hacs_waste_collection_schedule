import re
from datetime import datetime
import requests
import base64
import hashlib
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "APP Lipizzanerheimat"
DESCRIPTION = "Source for Lipizzanerheimat App"
COUNTRY = "at"
URL = "https://www.lipizzanerheimat.at"

APIKEY = 'bd75bdbc46162e4995a9'
APISECRET = '2c811f6c8f97eef2ed40'
USERNAME = 'mopedshop'
PASSWORD = 'T4P4qSur'

SERVICE_MAP = [
    {
        "title":  "Bärnbach",
        "url":  "https://baernbach.gv.at",
        "country":  "at",
    },
    {
        "title":  "Edelschrott",
        "url":  "https://www.edelschrott.gv.at",
        "country":  "at",
    },
    {
        "title":  "Geistthal-Södingberg",
        "url":  "https://geistthal-soedingberg.at",
        "country":  "at",
    },
    {
        "title":  "Hirschegg-Pack",
        "url":  "https://www.hirschegg-pack.gv.at",
        "country":  "at",
    },
    {
        "title":  "Kainach",
        "url":  "https://www.kainach.at",
        "country":  "at",
    },
    {
        "title":  "Köflach",
        "url":  "https://www.koeflach.at",
        "country":  "at",
    },
    {
        "title":  "Krottendorf-Gaisfeld",
        "url":  "https://www.krottendorf-gaisfeld.gv.at",
        "country":  "at",
    },
    {
        "title":  "Ligist",
        "url":  "https://www.ligist.gv.at",
        "country":  "at",
    },
    {
        "title":  "Maria Lankowitz",
        "url":  "https://www.maria-lankowitz.at",
        "country":  "at",
    },
    {
        "title":  "Mooskirchen",
        "url":  "https://www.mooskirchen.at",
        "country":  "at",
    },
    {
        "title":  "Rosental a.d Kainach",
        "url":  "https://www.rosental-kainach.at",
        "country":  "at",
    },
    {
        "title":  "Sankt Martin am Wöllmißberg",
        "url":  "https://st-martin-woellmissberg.gv.at",
        "country":  "at",
    },
    {
        "title":  "Söding-Sankt Johann",
        "url":  "https://www.soeding-st-johann.gv.at",
        "country":  "at",
    },
    {
        "title":  "Stallhofen",
        "url":  "https://www.stallhofen.gv.at",
        "country":  "at",
    },
    {
        "title":  "Voitsberg",
        "url":  "https://voitsberg.gv.at",
        "country":  "at",
    }
]

TEST_CASES = {
    # "Köflach - Debug": {"debug": True},
    "Köflach - Endgasse": {"town": "Köflach", "street": "Endgasse"},
    "Voitsberg - Bahnweg": {"garbage_calendar_id": 2437, },
    "Köflach - 8580 Köflach 1/7/9/13/30": {"map_name": '8580 Köflach 1/7/9/13/30', },
    "Voitsberg - Am Hügel": {"town": "Voitsberg", "street": "Am Hügel"},
    '8580 Köflach 1/13/14/30': {'map_name': '8580 Köflach 1/13/14/30'},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Open the Lipizzanerheimat app, login or use guest mode, select your town, go to the garbage calendar view and select the street you want to get the garbage collection dates for. You can either provide the calendar name in the lower center, the street name and town as written in the dropdown or provide the garbage_calendar_id directly.",
    "de": "Öffnen Sie die Lipizzanerheimat-App, melden Sie sich an oder nutzen Sie den Gastmodus, wählen Sie Ihre Stadt aus, gehen Sie zur Ansicht des Müllkalenders und wählen Sie die Straße aus, für die Sie die Müllabfuhrtermine erhalten möchten. Sie können entweder den Kalendernamen in der unteren Mitte, den Straßennamen und die Stadt, wie sie im Dropdown-Menü geschrieben sind, oder direkt die garbage_calendar_id angeben.",    "it": "COME OTTENERE GLI ARGOMENTI",
    "it": "Apri l'app Lipizzanerheimat, accedi o usa la modalità ospite, seleziona la tua città, vai alla vista del calendario dei rifiuti e seleziona la strada per cui desideri ottenere le date di raccolta dei rifiuti. Puoi fornire il nome del calendario nella parte inferiore centrale, il nome della strada e la città come scritto nel menu a discesa oppure fornire direttamente l'ID garbage_calendar_id."
}

PARAM_DESCRIPTIONS = {
    "en": {
        "garbage_calendar_id": "The ID of the garbage calendar to retrieve data for.",
        "street": "The street name to get garbage collection dates for.",
        "town": "The town corresponding to the selected street.",
        "map_name": "The name of the calendar map displayed in the app.",
    },
    "de": {
        "garbage_calendar_id": "Die ID des Müllkalenders, für den Daten abgerufen werden sollen.",
        "street": "Der Straßenname, für den die Müllabfuhrtermine abgerufen werden sollen.",
        "town": "Die Stadt, die zur ausgewählten Straße gehört.",
        "map_name": "Der Name der Kalenderkarte, die in der App angezeigt wird.",
    },
    "it": {
        "garbage_calendar_id": "L'ID del calendario dei rifiuti da cui recuperare i dati.",
        "street": "Il nome della strada per ottenere le date di raccolta dei rifiuti.",
        "town": "La città corrispondente alla strada selezionata.",
        "map_name": "Il nome della mappa del calendario mostrata nell'app.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "garbage_calendar_id": "Garbage Calendar ID",
        "street": "Street Name",
        "town": "Town",
        "map_name": "Calendar Map Name",
    },
    "de": {
        "garbage_calendar_id": "Müllkalender-ID",
        "street": "Straßenname",
        "town": "Stadt",
        "map_name": "Kalenderkartenname",
    },
    "it": {
        "garbage_calendar_id": "ID Calendario Rifiuti",
        "street": "Nome della Strada",
        "town": "Città",
        "map_name": "Nome della Mappa del Calendario",
    },
}
ICON_MAP = {
    "Müll": "mdi:trash-can",
    "Restmüll": "mdi:trash-can",
    "Restmüll - 8-wöchentlich": "mdi:trash-can",
    "Restmüll - 4-wöchentlich": "mdi:trash-can",
    "Restmüll - 2-wöchentlich": "mdi:trash-can",
    "Bioabfall": "mdi:fruit-watermelon",
    "Biomüll - wöchentlich": "mdi:fruit-watermelon",
    "Biomüll": "mdi:fruit-watermelon",
    "Biotonne": "mdi:fruit-watermelon",
    "Gefäßreinigung Bioabfall": "mdi:vacuum",
    "Behälterreinigung Bioabfall": "mdi:vacuum",
    "Sperrmüll": "mdi:sofa",
    "Glas": "mdi:glass-wine",
    "Spermüll - Alteisenabfuhr": "mdi:pot-mix-outline",
    "Altpapier": "mdi:package-variant",
    "Zwischenabfuhr Altpapier": "mdi:package-variant",
    "Problemstoffe": "mdi:chemical-weapon",
    "Problemstoffübernahme": "mdi:chemical-weapon",
    "Metallverpackung": "mdi:iron-outline",
    "Metall": "mdi:iron-outline",
    "Wirtschaftshof": "mdi:box-cutter",
    "Kunststoffverpackung": "mdi:recycle",
    'Leichtverpackung': 'mdi:recycle',
    "Kunststoff": "mdi:recycle",
    "Gelber Sack": "mdi:recycle",
    "Gelber Sack - 6-wöchentlich": "mdi:recycle",
    "Silofoliensammlung": "mdi:silo",
    'MET KKG': 'mdi:iron-outline',  # no idea...
    'ASZ': 'mdi:recycle',  # no idea...

}


def EXTRA_INFO():
    return [{"title": s["title"], "url": s["url"]} for s in SERVICE_MAP]


API_URL = "https://app.jolioo.com"


class Source:
    def __init__(self, garbage_calendar_id: int | None = None, street: str | None = None,  town: str | None = None, map_name: str | None = None):

        self.items = []
        self.icons = []

        self.garbage_calendar_id = garbage_calendar_id
        self.street = street
        self.town = town
        self.map_name = map_name

        self.default_headers = {
            'Host': 'app.jolioo.com',
            'User-Agent': 'okhttp/3.12.12',
            'Authorization': self.get_basic_auth_header(USERNAME, PASSWORD),
            'apikey': APIKEY,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    @staticmethod
    def sha1(input_str):
        return hashlib.sha1(input_str.encode('utf-8')).hexdigest()

    def api_hash(self, endpoint, payload):
        return self.sha1(f"{APISECRET}@{endpoint}@{payload}")

    @staticmethod
    def get_basic_auth_header(user, password):
        credentials = f"{user}:{password}"
        base64_credentials = base64.b64encode(
            credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {base64_credentials}"

    def sha1(self, input_str):
        return hashlib.sha1(input_str.encode('utf-8')).hexdigest()

    def build_header(self, url, payload):
        apihash = self.api_hash(url, payload)
        headers = self.default_headers
        headers['apihash'] = apihash
        return headers

    def fetch_communities(self):

        url = 'api/mobile-app/getcommunities'
        payload = 'language=de'

        headers = self.build_header(url, payload)

        communities = requests.request(
            "POST", f'{API_URL}/{url}', headers=headers, data=payload).json()['data']

        return next((c['community_id'] for c in communities if c['community_title'] == self.town), None)

    def fetch_calendar_id_by_name(self):

        url = 'api/mobile-app/garbagecalendarindexwithstreets'
        payload = f'language=de&communities=234|110|110|111|112|241|238|119|113|236|114|237|115|116|117|235&garbage_calendar_id=1'

        headers = self.build_header(url, payload)

        calendarData = requests.request(
            "POST", f'{API_URL}/{url}', headers=headers, data=payload).json()['data']

        return next((c['garbage_calendar_id']
                     for c in calendarData['garbage_calendars'] if c['garbage_calendar_title'] == self.map_name), None)

    def fetch_calendar_id(self):

        community_id = self.fetch_communities()

        if (community_id == None):
            raise SourceArgumentNotFound(
                [], "Town/Street combination not found.")

        url = 'api/mobile-app/garbagecalendarindexwithstreets'
        payload = f'language=de&communities={community_id}&garbage_calendar_id=1'

        headers = self.build_header(url, payload)

        response = requests.request(
            "POST", f'{API_URL}/{url}', headers=headers, data=payload)

        calendarData = response.json()['data']

        return next((c['garbage_calendars_available'][0]
                     for c in calendarData['street_structure'] if c['garbage_calendar_street'] == self.street), None)

    def _first_setup(self):

        r = requests.get(API_URL)

        if (self.street and self.town):
            garbage_calendar_id = self.fetch_calendar_id()
        elif (self.map_name):
            garbage_calendar_id = self.fetch_calendar_id_by_name()
        elif (self.garbage_calendar_id):
            garbage_calendar_id = self.garbage_calendar_id
        else:
            raise SourceArgumentException(
                [], "Please provide either `garbage_calendar_id`, `street` and `town`, or `map_name`.")

        payload = f'garbage_calendar_id={garbage_calendar_id}&language=de'
        url = 'api/mobile-app/garbagecalendar'

        headers = self.build_header(url, payload)

        data = requests.request(
            "POST", f'{API_URL}/{url}', headers=headers, data=payload).json()['data']

        if (len(data) == 0):
            raise SourceArgumentNotFound(
                [], "No data found for the provided arguments.")

        self.icons = {label["garbage_label_id"]: label["garbage_label_title"]
                      for label in data['labels']}

        self.items = data['items']

    def fetch(self) -> list[Collection]:

        self._first_setup()

        collections = []

        for item in self.items:
            garbageName = self.icons.get(item['garbage_label_id'])
            icon = ICON_MAP.get(garbageName)

            collections.append(
                Collection(
                    date=datetime.strptime(
                        item['garbage_calendar_item_date'], "%d.%m.%Y").date(),
                    t=garbageName,  # Collection type
                    icon=icon,  # Collection icon
                )
            )

        return collections
