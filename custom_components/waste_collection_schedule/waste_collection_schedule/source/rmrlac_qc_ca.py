import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "RMR Lac-Saint-Jean (QC)"
DESCRIPTION = "Source script for RMR Lac-Saint-Jean waste collection"
URL = "https://calendrier.rmrlac.qc.ca"
COUNTRY = "ca"

TEST_CASES = {
    "Métabetchouan-Lac-à-la-Croix (en)": {
        "street_number_and_name": "1201 16e Chemin",
        "locality": "Métabetchouan-Lac-à-la-Croix",
        "province_or_state": "QC",
        "language": "en",
    },
    "Métabetchouan-Lac-à-la-Croix (fr)": {
        "street_number_and_name": "1201 16e Chemin",
        "locality": "Métabetchouan-Lac-à-la-Croix",
        "province_or_state": "QC",
        "language": "fr",
    },
}

ICON_MAP = {
    "trash": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "compost": "mdi:leaf",
}

TYPE_MAP = {
    "fr": {
        "trash": "Déchets",
        "recycling": "Recyclage",
        "compost": "Matières organiques",
    },
    "en": {
        "trash": "Garbage",
        "recycling": "Recycling",
        "compost": "Organic",
    },
}

TYPE_KEYS = ["trash", "recycling", "compost"]

PARAM_DESCRIPTIONS = {
    "en": {
        "street_number_and_name": "Street number and name (e.g. '1201 16e Chemin')",
        "locality": "Municipality name (e.g. 'Métabetchouan-Lac-à-la-Croix')",
        "province_or_state": "Province or state code (default: QC)",
        "language": "Language code for collection type names (default: en, supported: en, fr)",
    },
    "fr": {
        "street_number_and_name": "Numéro et nom de rue (ex. '1201 16e Chemin')",
        "locality": "Nom de la municipalité (ex. 'Métabetchouan-Lac-à-la-Croix')",
        "province_or_state": "Province ou état (défaut: QC)",
        "language": "Code de langue pour les types de collecte (défaut: fr, supporté: en, fr)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_number_and_name": "Street Number and Name",
        "locality": "Municipality",
        "province_or_state": "Province/State",
        "language": "Language",
    },
    "fr": {
        "street_number_and_name": "Numéro et nom de rue",
        "locality": "Municipalité",
        "province_or_state": "Province/État",
        "language": "Langue",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street number and name along with your municipality.",
    "fr": "Entrez votre numéro et nom de rue ainsi que votre municipalite.",
}


def _submit_address(address: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 6) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "X-October-Request-Flash": "1",
        "X-October-Request-Handler": "wasteCollectionComposanteSearch0::onSubmitAddress",
        "X-October-Request-Partials": (
            "wasteCollectionComposanteSearch0::not-found&"
            "wasteCollectionComposanteSearch0::calendar"
        ),
        "sec-ch-ua": '"Chromium";v="148"',
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    body = (
        f"address={requests.utils.quote(address)}&localisation_lat=&localisation_lng="
    )

    r = requests.post(
        f"{URL}/calendrier-de-collectes",
        headers=headers,
        data=body.encode("utf-8"),
        params={
            "url": "/calendrier-de-collectes",
            "component": "wasteCollectionComposanteSearch0",
        },
    )
    r.raise_for_status()
    return r.json()


def _parse_entries(data: dict, lang: str = "en") -> list[Collection]:
    entries: list[Collection] = []

    not_found = data.get("wasteCollectionComposanteSearch0::not-found", "")
    if not_found and not_found.strip():
        raise SourceArgumentNotFound(
            argument="street_number_and_name",
            value="",
            message_addition="Address not found by RMR calendar system",
        )

    calendar_html = data.get("wasteCollectionComposanteSearch0::calendar", "")
    if not calendar_html:
        raise SourceArgumentNotFound(
            argument="street_number_and_name",
            value="",
            message_addition="No calendar returned for address",
        )

    soup = BeautifulSoup(calendar_html, "html.parser")
    calendar = soup.find("div", {"class": "collection-calendar"})
    if not calendar:
        raise SourceArgumentNotFound(
            argument="street_number_and_name",
            value="",
            message_addition="Calendar HTML not found",
        )

    fc_types = TYPE_MAP.get(lang, TYPE_MAP["en"])

    icon_types = [
        ("trash", "data-dates-trash"),
        ("recycling", "data-dates-recycling"),
        ("compost", "data-dates-compost"),
    ]

    for icon_key, attr in icon_types:
        dates_raw = calendar.get(attr, "").strip()
        if not dates_raw:
            continue

        fc_type = fc_types.get(icon_key)
        fc_icon = ICON_MAP.get(icon_key)
        if not fc_type:
            continue

        for date_str in dates_raw.split(","):
            date_str = date_str.strip()
            if not date_str:
                continue

            try:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue

            entries.append(Collection(date=dt.date(), t=fc_type, icon=fc_icon))

    return entries


class Source:
    def __init__(
        self,
        street_number_and_name: str,
        locality: str,
        province_or_state: str = "QC",
        language: str = "en",
    ):
        self._street_number_and_name = street_number_and_name
        self._locality = locality
        self._province_or_state = province_or_state
        self._language = language

    def fetch(self) -> list[Collection]:
        address = f"{self._street_number_and_name}, {self._locality}"
        data = _submit_address(address)
        entries = _parse_entries(data, lang=self._language)
        if not entries:
            raise SourceArgumentNotFound(
                argument="street_number_and_name",
                value=self._street_number_and_name,
                message_addition="Calendar found but no collections parsed",
            )
        return entries
