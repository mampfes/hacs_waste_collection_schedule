from datetime import datetime, timedelta

import requests
from dateutil.rrule import WEEKLY, rrule, weekday
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "App Backend of My Local Services"
DESCRIPTION = "Source for App Backend of My Local Services."
URL = "https://www.localcouncils.sa.gov.au"
TEST_CASES = {
    "35 Laurel Terrace; Robe SA 5276; Australia": {
        "lat": "-37.1647585",
        "lon": "139.7851318",
    },
    "18 Graeber Road, Lobethal SA 5241": {
        "lat": "-34.916506399999996",
        "lon": "138.8820226",
    },
    "25 Wyatt St, Mount Gambier SA 5290, Australia": {
        "lat": "-37.824624961239614",
        "lon": "140.77720893956482",
    },
    "-35.082943, 138.883702": {
        "lat": "-35.082943",
        "lon": "138.883702",
    },
}

EXTRA_INFO = [  # list from https://www.localcouncils.sa.gov.au/my-local-services-app#accordion__target-1426969-2
    {"url": "http://www.adelaidecitycouncil.com", "title": "City of Adelaide"},
    {"url": "https://www.ahc.sa.gov.au", "title": "Adelaide Hills Council"},
    {"url": "http://www.apc.sa.gov.au", "title": "Adelaide Plains Council"},
    {"url": "http://www.alexandrina.sa.gov.au", "title": "Alexandrina Council"},
    {"url": "http://www.berribarmera.sa.gov.au", "title": "Berri Barmera Council"},
    {"url": "http://www.campbelltown.sa.gov.au", "title": "Campbelltown City Council"},
    {"url": "http://www.burnside.sa.gov.au", "title": "City of Burnside"},
    {"url": "http://www.charlessturt.sa.gov.au", "title": "City of Charles Sturt"},
    {"url": "http://www.mountgambier.sa.gov.au", "title": "City of Mount Gambier"},
    {"url": "http://www.mitchamcouncil.sa.gov.au", "title": "City of Mitcham"},
    {
        "url": "https://www.npsp.sa.gov.au",
        "title": "City of Norwood Payneham and St Peters",
    },
    {"url": "http://www.onkaparingacity.com", "title": "City of Onkaparinga"},
    {
        "url": "https://www.cityofpae.sa.gov.au",
        "title": "City of Port Adelaide Enfield",
    },
    {"url": "http://www.prospect.sa.gov.au", "title": "City of Prospect"},
    {"url": "http://www.salisbury.sa.gov.au", "title": "City of Salisbury"},
    {"url": "http://www.westtorrens.sa.gov.au", "title": "City of West Torrens"},
    {"url": "http://www.whyalla.sa.gov.au", "title": "City of Whyalla"},
    {
        "url": "http://www.claregilbertvalleys.sa.gov.au",
        "title": "Clare and Gilbert Valleys Council",
    },
    {"url": "http://www.coorong.sa.gov.au", "title": "Coorong District Council"},
    {
        "url": "http://www.barungawest.sa.gov.au",
        "title": "District Council of Barunga West",
    },
    {"url": "http://www.cleve.sa.gov.au", "title": "District Council of Cleve"},
    {"url": "http://www.coppercoast.sa.gov.au", "title": "Council of Copper Coast"},
    {"url": "http://www.ceduna.sa.gov.au", "title": "District Council of Ceduna"},
    {"url": "http://www.elliston.sa.gov.au", "title": "District Council of Elliston"},
    {
        "url": "http://www.loxtonwaikerie.sa.gov.au",
        "title": "District Council of Loxton Waikerie",
    },
    {
        "url": "https://www.mountbarker.sa.gov.au",
        "title": "District Council of Mount Barker",
    },
    {
        "url": "https://www.mtr.sa.gov.au",
        "title": "District Council of Mount Remarkable",
    },
    {"url": "https://www.robe.sa.gov.au", "title": "District Council of Robe"},
    {
        "url": "http://www.streakybay.sa.gov.au",
        "title": "District Council of Streaky Bay",
    },
    {"url": "http://www.light.sa.gov.au", "title": "Light Regional Council"},
    {"url": "http://www.mid-murray.sa.gov.au", "title": "Mid Murray Council"},
    {
        "url": "http://www.naracoortelucindale.sa.gov.au",
        "title": "Naracoorte Lucindale Council",
    },
    {
        "url": "https://www.nacouncil.sa.gov.au/page.aspx",
        "title": "Northern Areas Council",
    },
    {"url": "http://www.portaugusta.sa.gov.au", "title": "Port Augusta City Council"},
    {"url": "http://www.pirie.sa.gov.au", "title": "Port Pirie Regional Council"},
    {"url": "http://www.goyder.sa.gov.au", "title": "Regional Council of Goyder"},
    {"url": "http://www.renmarkparinga.sa.gov.au", "title": "Renmark Paringa Council"},
    {
        "url": "http://www.murraybridge.sa.gov.au",
        "title": "Rural City of Murray Bridge",
    },
    {
        "url": "http://www.southernmallee.sa.gov.au",
        "title": "Southern Mallee District Council",
    },
    {
        "url": "http://www.frc.sa.gov.au/page.aspx",
        "title": "The Flinders Ranges Council",
    },
    {"url": "http://www.walkerville.sa.gov.au", "title": "Town of Walkerville"},
    {"url": "http://www.wakefieldrc.sa.gov.au", "title": "Wakefield Regional Council"},
    {"url": "http://www.yankalilla.sa.gov.au", "title": "Yankalilla District Council"},
    {"url": "http://yorke.sa.gov.au", "title": "Yorke Peninsula Council"},
    {
        "url": "https://fleurieuregionalwasteauthority.com.au",
        "title": "Fleurieu Regional Waste Authority",
    },
]

COUNTRY = "au"


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


API_URL = "https://services1.arcgis.com/37apdbovSVEwr4YE/ArcGIS/rest/services/MyLocalServices/FeatureServer/{endpoint}/query?f=pjson&geometry=%7B%22x%22:{lon},%22y%22:{lat},%22spatialReference%22:%7B%22wkid%22:4326%7D%7D&geometryType=esriGeometryPoint&inSR=4326&outFields=Waste_Type,Col_Day,Col_Freq,Colour,Col_Offset,Alternate,Exclusion,Additional&returnCountOnly=false&returnGeometry=false&returnIdsOnly=false&spatialRel=esriSpatialRelIntersects"
ENDPOINTS = (0, 1, 2, 4)


class Source:
    def __init__(self, lat: float, lon: float):
        if not isinstance(lat, float):
            try:
                lat = float(lat)
            except ValueError:
                raise ValueError("Latitude must be a float")
        if not isinstance(lon, float):
            try:
                lon = float(lon)
            except ValueError:
                raise ValueError("Longitude must be a float")

        self._lat: float = lat
        self._lon: float = lon

    def fetch(self) -> list[Collection]:
        # get json file
        entries = []
        for endpoint in ENDPOINTS:
            r = requests.get(
                API_URL.format(endpoint=endpoint, lat=self._lat, lon=self._lon)
            )
            r.raise_for_status()
            for features in r.json()["features"]:
                data = features["attributes"]
                exclusions_str: str | None = data["Exclusion"]
                additionals_str: str | None = data["Additional"]
                waste_type: str = data["Waste_Type"]

                weekday_int: int = (
                    data["Col_Day"] + -2
                ) % 7  # Normalise to 0(monday)-6(sunday) as response is 1(sunday)-7(saturday)
                freq: int = data["Col_Freq"]
                offset: int = data["Col_Offset"]

                start = datetime.now().replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                ).date() + timedelta(weeks=offset)
                end = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).date() + timedelta(days=365)

                dates = [
                    d.date()
                    for d in rrule(
                        WEEKLY,
                        byweekday=weekday(weekday_int),
                        interval=freq,
                        dtstart=start,
                        until=end,
                    )
                ]
                if additionals_str:
                    for additional_str in additionals_str.split(","):
                        dates.append(
                            datetime.strptime(additional_str.strip(), "%Y-%m-%d").date()
                        )
                if exclusions_str:
                    for exclusion_str in exclusions_str.split(","):
                        try:
                            dates.remove(
                                datetime.strptime(
                                    exclusion_str.strip(), "%Y-%m-%d"
                                ).date()
                            )
                        except ValueError:
                            print("Exclusion date not found in dates", exclusion_str)

                icon = ICON_MAP.get(waste_type.upper())  # Collection icon

                for d in dates:
                    entries.append(Collection(date=d, t=waste_type, icon=icon))

        return entries
