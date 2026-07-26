# Overview of the reverse-engineered API:
#
# - The public website only offers per-municipality PDF calendars, but they are extremely
#   difficult to parse because of many layout overlaps, garbled text streams, and
#   inconsistencies of several kinds. My pseudo-working draft for a PDF parser can be found
#   at the previous revision of this file, at commit 5a11eddaf5a3a83b90f687ed6be30eed9eb3c8f0
#
# - Sesa's mobile app (it.sesa.cordovaproject) however, is a Cordova webview that
#   interacts with a stateful PHP backend. Thanks to the excellent work of @lochmueller
#   on binable.app, I could discard that mess of a PDF parser (500+ locs) and base
#   this source on his findings. Some steps have changed since his implementation, or
#   in any case nothing is really self-documenting in this API so who knows. I did my
#   best to only replay the app's useful traffic, and I have reason to think all these
#   steps are essential. Removing some of them still leads to a JSON schedule, but it will
#   be from unspecified municipalities even if the address is set, with no error or notice.
# 
# The worflow is as follows:
#   1. POST /controller/controllerRegistration.php
#      This registers a new device uuid and opens a session.
#   2. GET /?p=new-indirizzo&uuid=X
#      This doesn't do anything but is essential. Above all, I don't know why it fails without the
#      uuid parameter if it's already associated to the session and no other request needs it.
#   3. POST /controller/controllerIndirizzi.php (with action=asyncAddress)
#      Set the municipality ID for the session
#   4. POST /controller/controllerUserSettings.php (with action=saveSettings)
#      This sets the chosen municipality for the session (again? Why.)
#   5. POST /controller/controllerCalendario.php (with action=calendario)
#      This will return a JSON response with the schedule. It is an array of:
#        {
#          "Giorno": "YYYY-MM-DD",
#          "Stile": "<div class=\"raccolta\"><div class=\"rifiuto secco\"><p>Secco<\/p><\/div><\/div>"
#        }
#      Instead of stripping and parsing the server-side rendered HTML it's probably
#      enough to just match class="rifiuto X" with a regex. Matching <p>X</p> might
#      lead to locale differences? Idk, didn't try.

import datetime
import re
import requests
import secrets
import logging

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import SourceArgAmbiguousWithSuggestions, SourceArgumentNotFound
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.icons import Icons


###############################################################################
##########           Integration's configuration constants           ##########
###############################################################################

TITLE = "S.E.S.A."
DESCRIPTION = "Source script for sesaeste.it"
SOURCE_CODEOWNERS = ['@AlexSartori']
URL = "https://sesaeste.it"
API_URL = 'https://app.sesaeste.it'

TEST_CASES = {
    "Legnaro": {"user_municipality": "Legnaro"},
    "Solesino": {"user_municipality": "Solesino"},
    "Polverara": {"user_municipality": "Polverara"}
}

ICON_MAP = {
    "PLASTICA LATTINE": Icons.PLASTIC_PACKAGING,
    "UMIDO": Icons.BIO_KITCHEN,
    "SECCO": Icons.GENERAL_WASTE,
    "CARTA": Icons.PAPER,
    "VETRO": Icons.GLASS,
    "VERDE": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "user_municipality": "Municipality",
    },
    "it": {
        "user_municipality": "Comune",
    },
}


###############################################################################
##########               Fetching and parsing logic                  ##########
###############################################################################

logger = logging.getLogger(__name__)


def _fetch_json_payload(municipality_name: str):
    s = requests.Session()
    s.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Android 14; Mobile; rv:148.0) Gecko/148.0 Firefox/148.0',
        'Referer': API_URL,
        'Cache-Control': 'no-cache'
    })

    # 1. Register our uuid and get a session
    uuid = secrets.token_hex(16)
    r = s.post(
        API_URL + '/controller/controllerRegistration.php', {
            'action': 'registration',
            'token': uuid,
            'uuid': uuid,
            'ip': '0.0.0.0',
            'platform': 'Android',
            'model': 'to mare omo',
            'lastLogin': datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
        }
    )
    r.raise_for_status()
    logger.info(f"{r.url}\t{r.status_code}")

    # 2. Mysterious essential step. Also, get the HTML list of municipalities.
    r = s.get(API_URL + '/?p=new-indirizzo&uuid=' + uuid)
    r.raise_for_status()
    municipality_id = _fetch_municipality_id(r.text, municipality_name)

    # 3. Set the municipality ID for the session
    r = s.post(
        API_URL + '/controller/controllerIndirizzi.php', {
            'action': 'asyncAddress',
            'comune': municipality_id
        }
    )
    r.raise_for_status()
    logger.info(f"{r.url}\t{r.status_code}")

    # 4. Save the settings (?)
    r = s.post(
        API_URL + '/controller/controllerUserSettings.php', {
            'action': 'saveSettings',
            'orario': -1,
            'comune': municipality_id,
            'notifiche': '0'
        }
    )
    r.raise_for_status()
    logger.info(f"{r.url}\t{r.status_code}")

    # 5. Get the schedule
    curr_year = datetime.datetime.today().year
    r = s.post(
        API_URL + '/controller/controllerCalendario.php', {
            'action': 'calendario',
            'today': f"{curr_year}-01-01",
            'lastday': f"{curr_year}-12-31"
        }
    )
    r.raise_for_status()
    logger.info(f"{r.url}\t{r.status_code}")

    return r.json()


def _fetch_municipality_id(html: str, municipality_name) -> str:
    html_cercacomune = BeautifulSoup(html, features="lxml")
    select = html_cercacomune.find('select', id="comuni", recursive=True)
    candidates: list[tuple[str, str]] = []

    if select is None:
        raise ValueError(f"The S.E.S.A. webapp HTML has an unexpected format and the list of municipalities could not be found.")

    for opt in select.find_all('option'):
        txt = opt.string
        val = opt.get('value')
        if txt is None or txt.strip() in ['', 'Comune'] or val is None:
            continue
        if txt.lower() == municipality_name.lower():
            candidates = [(str(val), txt)]
            break
        if municipality_name.lower() in txt.lower():
            candidates.append((str(val), txt))
    
    if len(candidates) == 0:
        raise SourceArgumentNotFound("user_municipality", municipality_name)
    if len(candidates) > 1:
        raise SourceArgAmbiguousWithSuggestions("user_municipality", municipality_name, [m for _, m in candidates])
    
    return candidates[0][0]


def _parse_json_to_schedule(json_data) -> list[Collection]:
    entries = []

    for item in json_data:
        d = datetime.date.strptime(item['Giorno'], "%Y-%m-%d")
        cat = re.findall(r'class="rifiuto (.+?)"', item['Stile'])
        for waste_type in cat:

            entries.append(Collection(
                date=d,
                t=waste_type.capitalize(),
                icon=ICON_MAP[waste_type.upper()]
            ))

    return entries


###############################################################################
##########                      Integration API                      ##########
###############################################################################

class Source:
    def __init__(self, user_municipality: str):
        self.user_municipality = user_municipality

    def fetch(self) -> list[Collection]:
        json_data = _fetch_json_payload(self.user_municipality)
        entries = _parse_json_to_schedule(json_data)

        return entries