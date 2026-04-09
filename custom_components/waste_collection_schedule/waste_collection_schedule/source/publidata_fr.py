import calendar
import logging
import re
from datetime import datetime, timedelta, timezone

import requests
from dateutil.rrule import (
    FR,
    MO,
    MONTHLY,
    SA,
    SU,
    TH,
    TU,
    WE,
    WEEKLY,
    rrule,
    rruleset,
)
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Publidata generic source"
DESCRIPTION = "Publidata is a French public operator with a reach of up to 6M inhabitants. Check if your area is concerned on their website."
URL = "https://www.publidata.io/fr/"
COUNTRY = "fr"

TEST_CASES = {
    "CASGBS, Le Pecq": {
        "address": "1 rue de Paris",
        "insee_code": "78481",
        "instance_id": 1420,
    },
    "GPSEO, Mantes la Ville": {
        "address": "11 rue Jean Moulin",
        "insee_code": "78362",
        "instance_id": 1294,
    },
    "Orleans Métropole, Boigny sur Bionne": {
        "address": "13 rue de la Commanderie",
        "insee_code": "45034",
        "instance_id": 100,
    },
    "Tours Métropole, Ballan-Miré": {
        "address": "3 Rue de Miré",
        "insee_code": "37018",
        "instance_id": 65,
    },
    # "Saumur Val de Loire, Allones": {
    # "address": "5 rue du Bellay",
    # "insee_code": "49002",
    # "instance_id": 159,
    # },
    # "Châteauroux Métropole, Ardentes": {
    # "address": "1 rue du 8 mai 1945",
    # "insee_code": "36005",
    # "instance_id": 897,
    # },
    # "Saint Quentin en Yvelines, Coignières": {
    # "address": "1 rue du four à chaux",
    # "insee_code": "78168",
    # "instance_id": 701,
    # },
    # "Versailles Grand Parc, Bailly": {
    # "address": "1 rue de Maule",
    # "insee_code": "78043",
    # "instance_id": 251,
    # },
    # "GPSO, Boulogne Billancourt": {
    # "address": "1 rue Gallieni",
    # "insee_code": "92012",
    # "instance_id": 101,
    # },
    # "ValEco, Bracieux": {
    # "address": "1 rue de Candy",
    # "insee_code": "41025",
    # "instance_id": 750,
    # },
    # "ValDem, Areines": {
    # "address": "1 rue de l’Ecole",
    # "insee_code": "41003",
    # "instance_id": 751,
    # },
    # "Dreux Agglomération, Ardelles": {
    # "address": "1 rue du Bourg Aubert",
    # "insee_code": "28008",
    # "instance_id": 725,
    # },
    # "Ardenne Métropole, Arreux": {
    # "address": "1 rue de la Vierge",
    # "insee_code": "08022",
    # "instance_id": 670,
    # },
    # "Dunkerque Grand Littoral, Bray-Dunes": {
    # "address": "1 rue Charles Pichon",
    # "insee_code": "59107",
    # "instance_id": 673,
    # },
    # "Grand Calais Terres et Mers, Calais": {
    # "address": "1 rue Martyn",
    # "insee_code": "62193",
    # "instance_id": 679,
    # },
    # "Métropole Européenne de Lille, Lille": {
    # "address": "34 Place Augustin Laurent",
    # "insee_code": "59350",
    # "instance_id": 876,
    # },
    # "Valcobreizh, Irodouër": {
    # "address": "1 rue de Rennes",
    # "insee_code": "35135",
    # "instance_id": "1003",
    # },
}

ICON_MAP = {
    "omr": "mdi:trash-can",
    "emb": "mdi:recycle",
    "enc": "mdi:truck-remove",
    "dv": "mdi:leaf",
    "verre": "mdi:bottle-wine",
    "bio": "mdi:food-apple",
    "sapin": "mdi:pine-tree",
}

LABEL_MAP = {
    "omr": "Ordures ménagères",
    "emb": "Emballages",
    "enc": "Encombrants",
    "dv": "Déchets verts",
    "verre": "Verres",
    "bio": "Biodéchets",
    "sapin": "Sapin",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address (number and street name only, without city or postcode). Find your commune's current INSEE code at https://www.insee.fr/fr/recherche/recherche-geographique — note that merged communes (communes nouvelles) have a new code. The instance_id is pre-filled when you select a known service provider.",
    "de": "Geben Sie Ihre Straßenadresse ein (nur Hausnummer und Straßenname, ohne Stadt oder Postleitzahl). Den aktuellen INSEE-Code Ihrer Gemeinde finden Sie unter https://www.insee.fr/fr/recherche/recherche-geographique — fusionierte Gemeinden (communes nouvelles) haben einen neuen Code. Die instance_id wird automatisch ausgefüllt, wenn Sie einen bekannten Dienstleister auswählen.",
    "it": "Inserisci il tuo indirizzo (solo numero civico e nome della via, senza città o codice postale). Trova il codice INSEE aggiornato del tuo comune su https://www.insee.fr/fr/recherche/recherche-geographique — i comuni uniti (communes nouvelles) hanno un nuovo codice. L'instance_id viene precompilato quando selezioni un fornitore noto.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address only (e.g. '4 rue de Paris'). Do not include city name or postcode.",
        "insee_code": "The 5-digit INSEE code of your commune. Check https://www.insee.fr if your commune has merged (communes nouvelles have a new code).",
        "instance_id": "Pre-filled when you select a known service provider. Only needed for unlisted providers (found via network inspector on the provider's waste widget).",
        "public_type": "Housing type filter (optional). Use 'individual_housing' for houses or 'collective_housing' for apartments if your area has different schedules per housing type.",
    },
    "de": {
        "address": "Nur Straßenadresse (z.B. '4 rue de Paris'). Keine Stadt oder Postleitzahl angeben.",
        "insee_code": "Der 5-stellige INSEE-Code Ihrer Gemeinde. Prüfen Sie https://www.insee.fr, ob Ihre Gemeinde fusioniert wurde (neuer Code).",
        "instance_id": "Wird automatisch ausgefüllt, wenn Sie einen bekannten Dienstleister wählen. Nur für nicht gelistete Anbieter nötig.",
        "public_type": "Wohnungstyp-Filter (optional). Verwenden Sie 'individual_housing' für Häuser oder 'collective_housing' für Wohnungen, wenn Ihr Gebiet unterschiedliche Abholpläne je Wohnungstyp hat.",
    },
    "it": {
        "address": "Solo indirizzo stradale (es. '4 rue de Paris'). Non includere città o codice postale.",
        "insee_code": "Il codice INSEE a 5 cifre del tuo comune. Verifica su https://www.insee.fr se il tuo comune è stato unito (nuovo codice).",
        "instance_id": "Precompilato quando selezioni un fornitore noto. Necessario solo per fornitori non elencati (trovato tramite ispettore di rete sul widget rifiuti del fornitore).",
        "public_type": "Filtro tipo abitazione (opzionale). Usare 'individual_housing' per case o 'collective_housing' per appartamenti se la zona ha calendari diversi per tipo di abitazione.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
        "insee_code": "INSEE Code",
        "instance_id": "Instance ID",
        "public_type": "Housing Type",
    },
    "de": {
        "address": "Adresse",
        "insee_code": "INSEE-Code",
        "instance_id": "Instanz-ID",
        "public_type": "Wohnungstyp",
    },
    "it": {
        "address": "Indirizzo",
        "insee_code": "Codice INSEE",
        "instance_id": "ID Istanza",
        "public_type": "Tipo Abitazione",
    },
}

EXTRA_INFO = [
    {
        "title": "CA Saint Germain Boucles de Seine",
        "url": "https://www.saintgermainbouclesdeseine.fr/",
        "default_params": {"instance_id": 1420},
    },
    {
        "title": "Grand Paris Seine et Oise",
        "url": "https://infos-dechets.gpseo.fr/",
        "default_params": {"instance_id": 1294},
    },
    {
        "title": "Orléans Métropole",
        "url": "https://triermondechet.orleans-metropole.fr/",
        "default_params": {"instance_id": 100},
    },
    {
        "title": "Tours Métropole",
        "url": "https://www.tours-metropole.fr/",
        "default_params": {"instance_id": 65},
    },
    {
        "title": "Saumur Val de Loire",
        "url": "https://www.saumurvaldeloire.fr/",
        "default_params": {"instance_id": 159},
    },
    {
        "title": "Châteauroux Métropole",
        "url": "https://www.chateauroux-metropole.fr/",
        "default_params": {"instance_id": 897},
    },
    {
        "title": "Saint Quentin en Yvelines",
        "url": "https://www.saint-quentin-en-yvelines.fr/",
        "default_params": {"instance_id": 701},
    },
    {
        "title": "Versailles Grand Parc",
        "url": "https://www.versaillesgrandparc.fr/",
        "default_params": {"instance_id": 251},
    },
    {
        "title": "Grand Paris Seine Ouest",
        "url": "https://www.dechets.seineouest.fr/",
        "default_params": {"instance_id": 101},
    },
    {
        "title": "ValEco",
        "url": "https://www.valeco41.fr/",
        "default_params": {"instance_id": 750},
    },
    {
        "title": "ValDem",
        "url": "https://www.valdem.fr/",
        "default_params": {"instance_id": 751},
    },
    {
        "title": "Dreux Agglomération",
        "url": "https://www.dreux-agglomeration.fr/",
        "default_params": {"instance_id": 725},
    },
    {
        "title": "Ardenne Métropole",
        "url": "https://www.ardenne-metropole.fr/",
        "default_params": {"instance_id": 670},
    },
    {
        "title": "Dunkerque Grand Littoral",
        "url": "https://www.mesinfosdechets.cud.fr/",
        "default_params": {"instance_id": 673},
    },
    {
        "title": "Grand Calais Terres et Mers",
        "url": "https://www.grandcalais.fr/",
        "default_params": {"instance_id": 679},
    },
    {
        "title": "Métropole Européenne de Lille",
        "url": "https://www.lillemetropole.fr/",
        "default_params": {"instance_id": 876},
    },
    {
        "title": "Valcobreizh",
        "url": "https://dechets.valcobreizh.fr",
        "default_params": {"instance_id": 1003},
    },
    {
        "title": "SIVOM Rive Droite",
        "url": "https://www.sivom-rivedroite.fr/",
        "default_params": {"instance_id": 1027},
    },
]

_CALENDAR_DAY_VERY_ABBR = {
    "Mo": MO,
    "Tu": TU,
    "We": WE,
    "Th": TH,
    "Fr": FR,
    "Sa": SA,
    "Su": SU,
}

_CALENDAR_MONTHS_ABBR = [m for m in calendar.month_abbr if m]

_LOGGER = logging.getLogger(__name__)


class Source:
    geocoder_url = "https://api.publidata.io/v2/geocoder"

    def __init__(
        self,
        address: str,
        insee_code: str,
        instance_id: int | str,
        public_type: str | None = None,
    ):
        self.address = address
        self.insee_code = insee_code
        self.instance_id = int(instance_id)
        self._public_type = public_type

    def _get_address_params(self, address, insee_code):
        params = {
            "q": address,
            "citycode": insee_code,
            "limit": 10,
            "lookup": "publidata",
        }
        response = requests.get(self.geocoder_url, params=params)

        if response.status_code != 200:
            raise SourceArgumentException("address", "Error response from geocoder")

        results = response.json()
        if not results:
            raise SourceArgumentException(
                "address",
                "No results found for the given address and INSEE code",
            )

        data = results[0].get("data", {}).get("features", [])
        if not data:
            raise SourceArgumentException(
                "address", "No results found for the given address and INSEE code"
            )

        lat, lon = data[0]["geometry"]["coordinates"]
        return {
            "lat": lat,
            "lon": lon,
            "address_id": data[0]["properties"]["id"],
        }

    def _perform_query(self):
        api_url = "https://api.publidata.io/v2/search"
        params = {
            "size": 999,
            "types[]": "Platform::Services::WasteCollection",
            "collection_modes[]": "truck",
            "instances[]": self.instance_id,
            **self.address_params,
        }
        if self._public_type:
            params["publics[]"] = "resident"
            params["public_types[]"] = self._public_type

        response = requests.get(api_url, params=params)

        if response.status_code != 200:
            raise Exception(
                f"Error fetching data from {api_url}: {response.status_code}"
            )

        return self._sanitize_response(response.json())

    def _sanitize_response(self, data):
        r"""
        Sanitize the response from the publidata API to extract the collection schedules for each type of waste.

        Example output:
        {
            "emb": {
                "schedules": [
                    {
                        "end_at": "2024-09-30T00:00:00.000+00:00",
                        "schedule_type": "closed",
                        "opening_hours": "2024 Jan 01-2024 Sep 30 off \"Fermeture\"",
                        "name": "Horaires de collecte",
                        "id": 1020853,
                        "start_at": "2024-01-01T00:00:00.000+00:00"
                    },
                    {
                        "end_at": "2024-12-29T00:00:00.000+00:00",
                        "schedule_type": "regular",
                        "opening_hours": "week 2-52/2 Mo 12:00-17:00",
                        "name": "Horaires de collecte",
                        "id": 1019827,
                        "start_at": "2024-01-08T00:00:00.000+00:00"
                    }
                ]
            },
            "omr": {
                "schedules": [
                    {
                    "end_at": "2024-09-30T00:00:00.000+00:00",
                    "schedule_type": "closed",
                    "opening_hours": "2024 Jan 01-2024 Sep 30 off \"Fermeture\"",
                    "name": "Horaires de collecte",
                    "id": 1020854,
                    "start_at": "2024-01-01T00:00:00.000+00:00"
                },
                {
                    "end_at": "2024-12-31T00:00:00.000+00:00",
                    "schedule_type": "regular",
                    "opening_hours": "Tu 05:00-12:00",
                    "name": "Horaires de collecte",
                    "id": 1019829,
                    "start_at": "2024-01-01T00:00:00.000+00:00"
                }
            ]
        }
        """
        result = {}
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            raise Exception("Unexpected response format")

        for hit in hits:
            source = hit.get("_source", {})
            if source.get("metas", {}).get("sectorization") == "single":
                garbage_type = source.get("metas", {}).get("garbage_types", [""])[0]
                if garbage_type:
                    result[garbage_type] = {"schedules": source.get("schedules", {})}
        return result

    def _is_week_day(self, input_string):
        return any(day in input_string for day in _CALENDAR_DAY_VERY_ABBR)

    def _parse_week_day(self, input_string):
        """Parse a string like "Mo" "Tu[2]", "We[2,4]" or "We,Th,Fr" and return the corresponding rrule.weekday object."""
        weekdays = []
        matches = re.findall(r"([A-Za-z]{2})(?:\[(\d+(?:,\d+)*)\])?", input_string)
        for day_of_week, nth_str in matches:
            if nth_str:
                nth = [int(n) for n in nth_str.split(",")]
                weekdays.extend([_CALENDAR_DAY_VERY_ABBR[day_of_week](n) for n in nth])
            else:
                weekdays.append(_CALENDAR_DAY_VERY_ABBR[day_of_week])

        if not weekdays:
            raise ValueError(f"Invalid day format: {input_string}")

        return {"byweekday": weekdays}

    def _is_time(self, input_string):
        return re.match(r"^(\d{2}:\d{2})|(24\/7)", input_string)

    def _is_day_number(self, input_string):
        return bool(re.match(r"^(\d{1,2})([,-]\d{1,2})*$", input_string))

    def _parse_day_number(self, input_string):
        return {"bymonthday": [int(day) for day in re.split("[,-]", input_string)]}

    def _is_month(self, input_string):
        return any(month in input_string for month in _CALENDAR_MONTHS_ABBR)

    def _parse_month(self, input_string):
        input_string = input_string.replace(
            ":", ""
        )  # match some actual cases in production
        if "-" in input_string:
            start_month, end_month = input_string.split("-")
            month_list = list(
                range(
                    _CALENDAR_MONTHS_ABBR.index(start_month) + 1,
                    _CALENDAR_MONTHS_ABBR.index(end_month) + 1,
                )
            )
        else:
            month_list = [
                _CALENDAR_MONTHS_ABBR.index(month) + 1
                for month in input_string.split(",")
            ]

        return {"bymonth": month_list}

    def _is_year(self, input_string):
        return bool(re.match(r"^(\d{4})", input_string))

    def _parse_year(self, input_string):
        if "-" in input_string:
            start_year, end_year = (int(year) for year in input_string.split("-"))
        elif "," in input_string:
            years = [int(year) for year in input_string.split(",")]
            if years != list(range(min(years), max(years) + 1)):
                raise ValueError(f"Invalid year range: {input_string}")
            start_year = min(years)
            end_year = max(years)
        else:
            start_year = int(input_string)
            end_year = start_year

        return {
            "dtstart": datetime(start_year, 1, 1, tzinfo=timezone.utc),
            "until": datetime(end_year, 12, 31, tzinfo=timezone.utc),
        }

    def _parse_part(self, part):
        """
        Parse a part of the opening_hours string and return the corresponding kwargs to rrule constructor.

        Example:
            "Sep-Nov" -> {"bymonth": [9, 10, 11]}
            "We[2,4]" -> {"byweekday": WE(2), WE(4)}
            "2024-2025" -> {"dtstart": datetime(2024, 1, 1, tzinfo=timezone.utc), "until": datetime(2025, 12, 31, tzinfo=timezone.utc)}
        """
        if self._is_year(part):
            return self._parse_year(part)
        elif self._is_month(part):
            return self._parse_month(part)
        elif self._is_week_day(part):
            return self._parse_week_day(part)
        elif self._is_day_number(part):
            return self._parse_day_number(part)
        elif self._is_time(part):
            return {}  # ignore those, the plugin doesn’t support time
        else:
            raise ValueError(f"Invalid part: {part}")

    def _parse_week_no(self, input_string):
        week_nos = []
        for sub_string in input_string.split(","):
            if "-" not in sub_string:
                week_nos.append(int(sub_string))
                continue

            weeks = sub_string.split("-")
            start_week = int(weeks[0])
            if "/" in weeks[1]:
                end_week = int(weeks[1].split("/")[0])
                interval = int(weeks[1].split("/")[1])
            else:
                end_week = int(weeks[1])
                interval = 1

            week_nos.extend(list(range(start_week, end_week + 1, interval)))

        return {"byweekno": week_nos}

    def _has_date_range(self, input_string):
        # Match both "2024 Jan 01-2024 May 12" and "Jan 01-Mar 14" formats
        return bool(
            re.search(r"^(\d{4} \w+ \d{1,2})-(\d{4} \w+ \d{1,2})", input_string)
            or re.search(r"^(\w+ \d{1,2})-(\w+ \d{1,2})", input_string)
        )

    def _extract_date_range(self, input_string):
        """Split a string containing a date range and return the range and remaining string.

        Handles formats like "2024 Jan 01-2024 May 12" or "Jan 01-Mar 14".
        """
        # Try to match format with year: "2024 Jan 01-2024 May 12"
        match = re.search(r"^(\d{4} \w+ \d{1,2}-\d{4} \w+ \d{1,2})(.*)", input_string)
        if match:
            return match.group(1), match.group(2).strip()

        # Try to match format without year: "Jan 01-Mar 14"
        match = re.search(r"^(\w+ \d{1,2}-\w+ \d{1,2})(.*)", input_string)
        if match:
            return match.group(1), match.group(2).strip()

        raise ValueError(f"Invalid date range: {input_string}")

    def _parse_date_range(self, input_string, default_year):
        """Parse a date range such as "2024 Jan 01-2024 May 12" or "Jan 01-Mar 14" and return the corresponding kwargs to rrule constructor.

        Args:
            input_string: The date range string to parse
            default_year: Year to use for date ranges without explicit year (e.g., "Jan 01-Mar 14")
        """
        parts = input_string.split("-")

        # Check if the first part starts with a year
        if (
            parts[0].strip().split()[0].isdigit()
            and len(parts[0].strip().split()[0]) == 4
        ):
            # Format: "2024 Jan 01-2024 May 12"
            start_date = datetime.strptime(parts[0] + " +0000", "%Y %b %d %z")
            end_date = datetime.strptime(parts[1] + " +0000", "%Y %b %d %z")
        else:
            # Format: "Jan 01-Mar 14" - use default_year or current year
            start_date = datetime.strptime(
                f"{default_year} {parts[0]} +0000", "%Y %b %d %z"
            )
            end_date = datetime.strptime(
                f"{default_year} {parts[1]} +0000", "%Y %b %d %z"
            )

        return {"dtstart": start_date, "until": end_date}

    def _parse_explicit_multi_dates(self, opening_hours):
        """Handle malformed Publidata format and return a list of explicit UTC datetimes.

        Parses formats like "2025 Jan 17,2026 Jan 16,2027 Jan 15 06:00-23:59".
        """
        if not opening_hours:
            return []

        pattern = (
            r"^(?:\d{4} [A-Za-z]{3} \d{1,2})"
            r"(?:,\d{4} [A-Za-z]{3} \d{1,2})+"
            r"(?: \d{2}:\d{2}-\d{2}:\d{2})?$"
        )
        if not re.match(pattern, opening_hours.strip()):
            return []

        explicit_dates = []
        for token in re.findall(r"\d{4} [A-Za-z]{3} \d{1,2}", opening_hours):
            explicit_dates.append(datetime.strptime(token + " +0000", "%Y %b %d %z"))

        return explicit_dates

    def _parse_schedule(self, schedule):
        """
        Parse a schedule and return a rrule object.

        Example input:
            "end_at": "2025-07-16T00:00:00.000+00:00",
            "opening_hours": "week 2-52/2 Mo 12:00-17:00",
            "name": "Horaires de collecte",
            "id": 1019827,
            "start_at": "2024-01-08T00:00:00.000+00:00"

        Return:
            rrule object


        Handled opening_hours formats:
            "week 2-52/2 Mo 12:00-17:00"
            "Feb,May,Aug,Nov Th[4] 05:00-12:00"
            "Tu 05:00-12:00"
            "2025 Jul 16 05:00-12:00"
            "2025 Jul 16 off"
            "2025 Jan,Apr,Jul,Oct Tu[1] 05:00-12:00"
            "2024-2025 Mo 05:00-12:00"
            "2024-2025 Dec: We[2,4] 09:00-19:00"
            "2024-2025 Sep-Nov We 09:00-19:00"
            "week 18 Mo,Fr 14:00-18:00"
            "week 1-52 Mo 12:00-17:00"
            "week 1-17,19-52 Mo,We,Fr 14:00-18:00"
            "2024,2025 week 1-17,19-52 Mo,We,Fr 14:00-18:00"
            "2024 Jan 01-2024 May 12 week 01-53/2 Mo"
            "Jan 01-Mar 14 off "Fermeture"
        """
        start_date = (
            datetime.strptime(schedule["start_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
            if schedule["start_at"]
            else None
        )

        if (
            schedule["end_at"] and schedule["schedule_type"] != "regular"
        ):  # publidata seems to somehow disregard this field
            end_date = datetime.strptime(schedule["end_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            end_date = datetime.now(timezone.utc) + timedelta(days=365)

        opening_hours = schedule["opening_hours"]

        kwargs = {
            "freq": MONTHLY,
            "dtstart": start_date,
            "until": end_date,
        }

        if self._has_date_range(opening_hours):
            date_range, opening_hours = self._extract_date_range(opening_hours)
            default_year = (
                start_date.year if start_date else datetime.now(timezone.utc).year
            )
            kwargs.update(self._parse_date_range(date_range, default_year))

        parts = opening_hours.split()
        while parts:
            part = parts.pop(0)
            if part == "week":
                kwargs["freq"] = WEEKLY
                kwargs.update(self._parse_week_no(parts.pop(0)))
            elif part.startswith("off") or part.startswith(
                '"'
            ):  # schedule should be of type "closed" or "closing_exception", or part should be a comment
                continue
            else:
                kwargs.update(self._parse_part(part))

        # Create the rrule
        rule = rrule(**kwargs)

        return rule

    def fetch(self):
        self.address_params = self._get_address_params(self.address, self.insee_code)

        entries = []

        sanitized_response = self._perform_query()
        for waste_type, waste_data in sanitized_response.items():
            my_rruleset = rruleset()
            for schedule in waste_data["schedules"]:
                schedule_type = schedule.get("schedule_type")

                try:
                    parsed_schedule = self._parse_schedule(schedule)
                    if schedule_type in ("regular", "exception"):
                        my_rruleset.rrule(parsed_schedule)
                    elif schedule_type in ("closed", "closing_exception"):
                        my_rruleset.exrule(parsed_schedule)
                    continue
                except Exception as err:
                    explicit_dates = self._parse_explicit_multi_dates(
                        schedule.get("opening_hours", "")
                    )
                    if explicit_dates:
                        if schedule_type in ("regular", "exception"):
                            for explicit_date in explicit_dates:
                                my_rruleset.rdate(explicit_date)
                        elif schedule_type in ("closed", "closing_exception"):
                            for explicit_date in explicit_dates:
                                my_rruleset.exdate(explicit_date)
                        continue

                    _LOGGER.warning(
                        "Skipping invalid Publidata schedule id=%s opening_hours=%r: %s",
                        schedule.get("id"),
                        schedule.get("opening_hours"),
                        err,
                    )
                    continue
            for entry in my_rruleset:
                entries.append(
                    Collection(
                        entry.date(),
                        LABEL_MAP.get(waste_type, waste_type.capitalize()),
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
