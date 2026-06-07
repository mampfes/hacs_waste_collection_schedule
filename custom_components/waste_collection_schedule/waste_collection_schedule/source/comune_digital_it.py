from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Comune.Digital"
DESCRIPTION = "Source for Italian municipalities using the Comune.Digital (GoodBarber) app platform."
URL = "https://comune.digital"
COUNTRY = "it"

TEST_CASES = {
    "Santo Stefano di Camastra": {
        "city": "santostefanodicamastra",
    },
}

ICON_MAP = {
    "umido": Icons.BIO_KITCHEN,
    "organico": Icons.ORGANIC,
    "secco": Icons.GENERAL_WASTE,
    "carta": Icons.PAPER,
    "cartone": Icons.PAPER,
    "plastica": Icons.PLASTIC_PACKAGING,
    "vetro": Icons.GLASS,
    "ingombranti": Icons.BULKY,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "The city identifier is the subdomain of your municipality's Comune.Digital website. "
    "For example, if the website is https://santostefanodicamastra.comune.digital, "
    'the city identifier is "santostefanodicamastra".',
    "it": "L'identificatore della città è il sottodominio del sito web Comune.Digital del tuo comune. "
    "Ad esempio, se il sito è https://santostefanodicamastra.comune.digital, "
    'l\'identificatore è "santostefanodicamastra".',
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City identifier",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Subdomain of the Comune.Digital website (e.g. santostefanodicamastra)",
    },
}

SETTINGS_URL = "https://{city}.comune.digital/apiv4/getSettings?platform=webapp"
ITEMS_URL = "https://api.ww-api.com/front/get_items/{webzine_id}/{section_id}/"
SECTION_TYPE = "GBModuleTypeAgenda"
WASTE_KEYWORDS = ("differenziata", "rifiut", "raccolt", "spazzatura")


def _get_icon(title: str) -> str | None:
    title_lower = title.lower()
    for keyword, icon in ICON_MAP.items():
        if keyword in title_lower:
            return icon
    return None


class Source:
    def __init__(self, city: str) -> None:
        self._city = city.strip().lower()

    def fetch(self) -> list[Collection]:
        # Step 1: Discover webzine_id and waste section_id
        settings_url = SETTINGS_URL.format(city=self._city)
        resp = requests.get(settings_url, timeout=30)
        if resp.status_code == 404:
            raise SourceArgumentNotFound(
                "city",
                self._city,
                "City not found on comune.digital. Check the subdomain is correct.",
            )
        resp.raise_for_status()

        data = resp.json()
        webzine_id = data.get("idWebzine")
        if not webzine_id:
            raise SourceArgumentNotFound(
                "city",
                self._city,
                "Could not retrieve webzine ID from comune.digital.",
            )

        gs = data.get("gbsettings", {})
        sections = gs.get("sections", {})

        section_id = self._find_waste_section(sections)
        if not section_id:
            raise SourceArgumentNotFound(
                "city",
                self._city,
                "No waste-collection schedule section found for this city on comune.digital.",
            )

        # Step 2: Fetch all waste-collection events (paginate while items are returned)
        entries: list[Collection] = []
        page = 1
        per_page = 100

        while True:
            items_url = ITEMS_URL.format(webzine_id=webzine_id, section_id=section_id)
            resp = requests.get(
                items_url,
                params={"page": page, "per_page": per_page},
                timeout=30,
            )
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("items", [])
            if not items:
                break

            for item in items:
                raw_date_str = item.get("sortDate") or item.get("date", "")
                if not raw_date_str:
                    continue
                title: str = item.get("title", "").strip()
                if not title:
                    continue

                # Parse ISO datetime and extract the date portion.
                # Events are "Stasera esporre …" (Tonight put out …) at 20:00 —
                # the bin is actually collected the following morning, so we
                # advance the date by one day.
                try:
                    event_date = date.fromisoformat(raw_date_str[:10])
                except ValueError:
                    continue

                collection_date = event_date + timedelta(days=1)

                # Strip the "Stasera esporre " prefix when present to get the
                # clean waste-type string shown to the user.
                waste_type = title
                for prefix in ("Stasera esporre ", "stasera esporre "):
                    if waste_type.startswith(prefix):
                        waste_type = waste_type[len(prefix) :].capitalize()
                        break

                icon = _get_icon(waste_type)
                entries.append(
                    Collection(date=collection_date, t=waste_type, icon=icon)
                )

            page += 1

        return entries

    @staticmethod
    def _find_waste_section(sections: dict) -> str | None:
        """Return the section_id of the first Agenda section whose title
        contains a waste-collection keyword."""
        for section_id, section_data in sections.items():
            if not isinstance(section_data, dict):
                continue
            if section_data.get("type") != SECTION_TYPE:
                continue
            title: str = section_data.get("title", "").lower()
            if any(kw in title for kw in WASTE_KEYWORDS):
                return section_id
        return None
