import datetime
import requests

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Oslo Kommune"
DESCRIPTION = "Oslo Kommune (Norway)."
URL = "https://www.oslo.kommune.no"

# **street_id:** \
# Can be found with this REST-API call.
# ```
# https://ws.geonorge.no/adresser/v1/#/default/get_sok
# https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012
# ```
# "street_id" equals to "adressekode".

TEST_CASES = {
    "Villa Paradiso": {
        "street_name": "Olaf Ryes Plass",
        "house_number": 8,
        "house_letter": '',
        "street_id": 15331
    },
    "Nåkkves vei": {
        "street_name": "Nåkkves vei",
        "house_number": 5,
        "house_letter": '',
        "street_id": 15280,
        "point_id": 38175
    }
}

API_URL = "https://www.oslo.kommune.no/actions/snap-lib-waste-complaint/search-by-address"
ICON_MAP = {
    "":           "mdi:trash-can",
    "restavfall": "mdi:trash-can",
    "papir":      "mdi:newspaper-variant-multiple"
}

# Map Hyppighet.Faktor to interval in days
FREQUENCY_DAYS = {
    10000: 7,    # 1 gang pr. uke (weekly)
    20000: 4,    # 2 ganger pr. uke (twice weekly, approximate)
    30000: 3,    # 3 ganger pr. uke (three times weekly, approximate)
    40000: 14,   # annenhver uke (every other week)
    50000: 28,   # 1 gang pr. måned (monthly)
}
DEFAULT_INTERVAL_DAYS = 7

# ### Arguments affecting the configuration GUI ####

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "point_id": "Optional waste point ID to filter by",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "point_id": "Point ID",
    },
}

# ### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(
        self,
        street_name: str,
        house_number: int,
        street_id: int,
        house_letter: str | None = None,
        point_id: int | None = None,
    ):
        self._street_name = street_name
        self._house_number = house_number
        self._street_id = street_id
        self._house_letter = house_letter
        self._point_id = point_id

    def fetch(self):
        params = {
            "street": self._street_name,
            "number": self._house_number,
            "street_id": self._street_id,
        }
        if self._house_letter:
            params["letter"] = self._house_letter

        headers = {
            "Accept": "application/json",
        }

        r = requests.get(API_URL, params=params, headers=headers, timeout=30)
        r.raise_for_status()

        today = datetime.date.today()
        entries = []
        data = r.json()
        res = data["result"][0]["HentePunkts"]
        for f in res:
            if self._point_id and int(f["Id"]) != int(self._point_id):
                continue

            tjenester = f["Tjenester"]
            for tjeneste in tjenester:
                tekst = tjeneste["Fraksjon"]["Tekst"]
                tomme_date = datetime.datetime.strptime(
                    tjeneste["TommeDato"], "%d.%m.%Y"
                ).date()

                if tomme_date >= today:
                    # TommeDato is in the future (or today), use it directly
                    entries.append(
                        Collection(
                            date=tomme_date,
                            t=tekst,
                            icon=ICON_MAP.get(tekst.lower(), "mdi:trash-can"),
                        )
                    )
                else:
                    # TommeDato is in the past — calculate upcoming dates
                    # from the last collection date and frequency
                    faktor = tjeneste.get("Hyppighet", {}).get("Faktor", 0)
                    interval = FREQUENCY_DAYS.get(faktor, DEFAULT_INTERVAL_DAYS)

                    date = tomme_date + datetime.timedelta(days=interval)
                    while date < today:
                        date += datetime.timedelta(days=interval)
                    for _ in range(8):
                        entries.append(
                            Collection(
                                date=date,
                                t=tekst,
                                icon=ICON_MAP.get(tekst.lower(), "mdi:trash-can"),
                            )
                        )
                        date += datetime.timedelta(days=interval)

        return entries
