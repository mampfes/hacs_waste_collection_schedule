import logging
from datetime import date, datetime, timedelta
from typing import ClassVar, final

from dateutil.rrule import WEEKLY, rrule, weekday
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import coords
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    feature_query,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

# My Local Services (used by ~45 South Australian councils) takes a lat/lon
# straight from the map picker: there's no address to geocode, so the shared
# ArcGIS retrievers (which hard-code a geocode() call) don't fit. retrieve()
# spatially queries the four FeatureServer layers directly at that point.
# Each matched feature also carries its own recurring cadence (a weekday, a
# frequency in weeks and a phase offset) plus provider-supplied additive and
# exclusion date lists that adjust the projected schedule -- more than
# RecurrenceExpander/HolidayShift express (they shift/cancel *existing* rows,
# they don't also splice in dates that aren't part of the cadence at all), so
# preprocess() projects the cadence and applies both adjustments itself,
# unchanged from the legacy implementation.

_LOGGER = logging.getLogger(__name__)

FEATURE_SERVER = (
    "https://services1.arcgis.com/37apdbovSVEwr4YE/ArcGIS/rest/services/"
    "MyLocalServices/FeatureServer"
)
LAYERS = (0, 1, 2, 4)
OUT_FIELDS = (
    "Waste_Type,Col_Day,Col_Freq,Colour,Col_Offset,Alternate,Exclusion,Additional"
)
SCHEDULE_DAYS = 365

_TYPE_MAP = {
    "General Waste": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
    "Green Waste": GARDEN_WASTE,
    "FOGO (Organics)": ORGANIC,
}

# List from https://www.localcouncils.sa.gov.au/my-local-services-app#accordion__target-1426969-2
_COUNCILS = [
    ("City of Adelaide", "http://www.adelaidecitycouncil.com"),
    ("Adelaide Hills Council", "https://www.ahc.sa.gov.au"),
    ("Adelaide Plains Council", "http://www.apc.sa.gov.au"),
    ("Alexandrina Council", "http://www.alexandrina.sa.gov.au"),
    ("Berri Barmera Council", "http://www.berribarmera.sa.gov.au"),
    ("Campbelltown City Council", "http://www.campbelltown.sa.gov.au"),
    ("City of Burnside", "http://www.burnside.sa.gov.au"),
    ("City of Charles Sturt", "http://www.charlessturt.sa.gov.au"),
    ("City of Mount Gambier", "http://www.mountgambier.sa.gov.au"),
    ("City of Mitcham", "http://www.mitchamcouncil.sa.gov.au"),
    ("City of Norwood Payneham and St Peters", "https://www.npsp.sa.gov.au"),
    ("City of Onkaparinga", "http://www.onkaparingacity.com"),
    ("City of Port Adelaide Enfield", "https://www.cityofpae.sa.gov.au"),
    ("City of Prospect", "http://www.prospect.sa.gov.au"),
    ("City of Salisbury", "http://www.salisbury.sa.gov.au"),
    ("City of West Torrens", "http://www.westtorrens.sa.gov.au"),
    ("City of Whyalla", "http://www.whyalla.sa.gov.au"),
    ("Clare and Gilbert Valleys Council", "http://www.claregilbertvalleys.sa.gov.au"),
    ("Coorong District Council", "http://www.coorong.sa.gov.au"),
    ("District Council of Barunga West", "http://www.barungawest.sa.gov.au"),
    ("District Council of Cleve", "http://www.cleve.sa.gov.au"),
    ("Council of Copper Coast", "http://www.coppercoast.sa.gov.au"),
    ("District Council of Ceduna", "http://www.ceduna.sa.gov.au"),
    ("District Council of Elliston", "http://www.elliston.sa.gov.au"),
    ("District Council of Loxton Waikerie", "http://www.loxtonwaikerie.sa.gov.au"),
    ("District Council of Mount Barker", "https://www.mountbarker.sa.gov.au"),
    ("District Council of Mount Remarkable", "https://www.mtr.sa.gov.au"),
    ("District Council of Robe", "https://www.robe.sa.gov.au"),
    ("District Council of Streaky Bay", "http://www.streakybay.sa.gov.au"),
    ("Light Regional Council", "http://www.light.sa.gov.au"),
    ("Mid Murray Council", "http://www.mid-murray.sa.gov.au"),
    ("Naracoorte Lucindale Council", "http://www.naracoortelucindale.sa.gov.au"),
    ("Northern Areas Council", "https://www.nacouncil.sa.gov.au/page.aspx"),
    ("Port Augusta City Council", "http://www.portaugusta.sa.gov.au"),
    ("Port Pirie Regional Council", "http://www.pirie.sa.gov.au"),
    ("Regional Council of Goyder", "http://www.goyder.sa.gov.au"),
    ("Renmark Paringa Council", "http://www.renmarkparinga.sa.gov.au"),
    ("Rural City of Murray Bridge", "http://www.murraybridge.sa.gov.au"),
    ("Southern Mallee District Council", "http://www.southernmallee.sa.gov.au"),
    ("The Flinders Ranges Council", "http://www.frc.sa.gov.au/page.aspx"),
    ("Town of Walkerville", "http://www.walkerville.sa.gov.au"),
    ("Wakefield Regional Council", "http://www.wakefieldrc.sa.gov.au"),
    ("Yankalilla District Council", "http://www.yankalilla.sa.gov.au"),
    ("Yorke Peninsula Council", "http://yorke.sa.gov.au"),
    (
        "Fleurieu Regional Waste Authority",
        "https://fleurieuregionalwasteauthority.com.au",
    ),
]


@final
class Source(BaseSource):
    TITLE = "App Backend of My Local Services"
    DESCRIPTION = "Source for App Backend of My Local Services."
    URL = "https://www.localcouncils.sa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
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

    REGIONS = tuple(region(title=title, url=url) for title, url in _COUNCILS)

    PARAMS = (coords(),)

    parse = ArcGisMultiFeatureParser()
    transform = RowTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, lat, lon):
        if not isinstance(lat, float):
            try:
                lat = float(lat)
            except ValueError:
                raise ValueError("Latitude must be a float") from None
        if not isinstance(lon, float):
            try:
                lon = float(lon)
            except ValueError:
                raise ValueError("Longitude must be a float") from None
        super().__init__(lat=lat, lon=lon)

    def retrieve(self, source: "Source"):
        location = {"x": self.params["lon"], "y": self.params["lat"]}
        return [
            (
                endpoint,
                feature_query(
                    f"{FEATURE_SERVER}/{endpoint}",
                    geometry=location,
                    out_fields=OUT_FIELDS,
                    timeout=self.TIMEOUT,
                ),
            )
            for endpoint in LAYERS
        ]

    def preprocess(self, records, source=None):
        for _endpoint, attrs in records:
            yield from self._expand(attrs)

    @staticmethod
    def _expand(attrs):
        exclusions_str: str | None = attrs["Exclusion"]
        additionals_str: str | None = attrs["Additional"]
        waste_type: str = attrs["Waste_Type"]

        # Normalise to 0(Monday)-6(Sunday); the API returns 1(Sunday)-7(Saturday).
        weekday_int: int = (attrs["Col_Day"] + -2) % 7
        freq: int = attrs["Col_Freq"]
        offset: int = attrs["Col_Offset"]

        start = datetime.now().replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        ).date() + timedelta(weeks=offset)
        end = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).date() + timedelta(days=SCHEDULE_DAYS)

        dates: list[date] = [
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
                        datetime.strptime(exclusion_str.strip(), "%Y-%m-%d").date()
                    )
                except ValueError:
                    _LOGGER.debug(
                        "Exclusion date not found in dates: %s", exclusion_str
                    )

        for d in dates:
            yield d, waste_type
