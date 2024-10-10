import calendar
import re
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException
from datetime import datetime, timedelta, timezone
from dateutil.rrule import rruleset, rrule, WEEKLY, MONTHLY, DAILY, MO, TU, WE, TH, FR, SA, SU

TITLE = "Generic source for publidata-based waste schedule management"
DESCRIPTION = "Publidata is a French public operator with a reach of up to 6M inhabitants. Check if your area is concerned on their website."
URL = "https://www.publidata.io/fr/"
COUNTRY = "fr"

TEST_CASES = {
    "GPSEO, Mantes la Ville": {"address": "11 rue Jean Moulin", "insee_code": "78362", "instance_id": 1292},
    "GPSEO, Villennes sur Seine": {"address": "157 rue maurice utrillo", "insee_code": "78672", "instance_id": 1292},
    "GPSEO, Poissy": {"address": "77 avenue Maurice Berteaux", "insee_code": "78498", "instance_id": 1292},
    "Orleans Métropole, Boigny sur Bionne": {"address": "13 rue de la Commanderie", "insee_code": "45034", "instance_id": 100},
    "Tours Métropole, Ballan-Miré": {"address": "3 Rue de Miré", "insee_code": "37018", "instance_id": 65},
}

ICON_MAP = {
    "omr": "mdi:trash-can",
    "emb": "mdi:bottle-soda",
    "enc": "mdi:leaf",
    "dv": "mdi:package-variant",
    "verre": "mdi:recycle",
}

LABEL_MAP = {
    "omr": "Ordures ménagères",
    "emb": "Emballages",
    "enc": "Encombrants",
    "dv": "Déchets verts",
    "verre": "Verres",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "The INSEE code of your commune is easily found on google. instance_id can be found through a network inspecter from the official widget",
    "de": "Der INSEE-Code Ihrer Gemeinde kann leicht über Google gefunden werden. Die instance_id kann durch einen Netzwerk-Inspektor vom offiziellen Widget ermittelt werden",
    "it": "Il codice INSEE del tuo comune si trova facilmente su Google. L'instance_id può essere trovato attraverso un ispettore di rete dal widget ufficiale",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your full address",
        "insee_code": "The 5-digit INSEE code of your commune",
        "instance_id": "An identifier of your waste collection service. For examlpe GPSEO's is 1292 and found by inspecting the network calls on https://infos-dechets.gpseo.fr/4E79YtZv7M/list/?addressId=78005_0073_00002",
    },
    "de": {
        "address": "Ihre vollständige Adresse",
        "insee_code": "Der 5-stellige INSEE-Code Ihrer Gemeinde",
        "instance_id": "Eine Kennung Ihres Abfallsammeldienstes. Zum Beispiel ist die von GPSEO 1292 und kann durch Inspektion der Netzwerkaufrufe auf https://infos-dechets.gpseo.fr/4E79YtZv7M/list/?addressId=78005_0073_00002 gefunden werden",
    },
    "it": {
        "address": "Il tuo indirizzo completo",
        "insee_code": "Il codice INSEE a 5 cifre del tuo comune",
        "instance_id": "Un identificatore del tuo servizio di raccolta rifiuti. Ad esempio, quello di GPSEO è 1292 e si trova ispezionando le chiamate di rete su https://infos-dechets.gpseo.fr/4E79YtZv7M/list/?addressId=78005_0073_00002",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
        "insee_code": "INSEE Code",
        "instance_id": "Instance ID",
    },
    "de": {
        "address": "Adresse",
        "insee_code": "INSEE-Code",
        "instance_id": "Instanz-ID",
    },
    "it": {
        "address": "Indirizzo",
        "insee_code": "Codice INSEE",
        "instance_id": "ID Istanza",
    },
}

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

class Source:
    geocoder_url = "https://api.publidata.io/v2/geocoder"

    def __init__(self, address, insee_code, instance_id):
        self.address = address
        self.insee_code = insee_code
        self.instance_id = instance_id

            
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
        
        data = response.json()[0]['data']['features']
        if not data:
            raise SourceArgumentException("address", "No results found for the given address and INSEE code")
        
        lat, lon = data[0]['geometry']['coordinates']
        return {
            "lat": lat,
            "lon": lon,
            "address_id": data[0]['properties']['id'],
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
        
        response = requests.get(api_url, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Error fetching data from {api_url}: {response.status_code}") # TODO: Check if this is the correct exception to raise
        
        return self._sanitize_response(response.json())
    
    def _sanitize_response(self, data):
        """
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
        hits = data.get('hits', {}).get('hits', [])
        if not hits:
            raise Exception("TODO")
        
        for hit in hits:
            source = hit.get('_source', {})
            if source.get('metas', {}).get('sectorization') == 'single':
                garbage_type = source.get('metas', {}).get('garbage_types', [''])[0]
                if garbage_type:
                    result[garbage_type] = {'schedules': source.get('schedules', {})}
        return result
            
    def _parse_closure(self, schedule):
        """
        Parse a closure schedule and return a daily rrule between the start and end dates.
        """
        start_date = datetime.strptime(schedule['start_at'], '%Y-%m-%dT%H:%M:%S.%f%z')
        end_date = datetime.strptime(schedule['end_at'], '%Y-%m-%dT%H:%M:%S.%f%z')
        return rrule(
            freq=DAILY,
            dtstart=start_date,
            until=end_date
        )
                   
    def _is_week_day(self, input_string):
        return any(day in input_string for day in _CALENDAR_DAY_VERY_ABBR)
            
    def _parse_week_day(self, input_string):
        """
        parse a string like "Mo" "Tu[2]", "We[2,4]" or "We,Th,Fr" and return the corresponding rrule.weekday object
        """
        weekdays = []
        matches = re.findall(r'([A-Za-z]{2})(?:\[(\d+(?:,\d+)*)\])?', input_string)
        for day_of_week, nth_str in matches:
            if nth_str:
                nth = [int(n) for n in nth_str.split(',')]
                weekdays.extend([_CALENDAR_DAY_VERY_ABBR[day_of_week](n) for n in nth])
            else:
                weekdays.append(_CALENDAR_DAY_VERY_ABBR[day_of_week])

        if not weekdays:
            raise ValueError(f"Invalid day format: {day}")
        
        return {"byweekday": weekdays}
            
    def _is_time(self, input_string):
        return re.match(r'^(\d{2}:\d{2})', input_string)
            
    def _is_day_number(self, input_string):
        return bool(re.match(r'^(\d{1,2})(,\d{1,2})*$', input_string))
            
    def _parse_day_number(self, input_string):
        return {"bymonthday": [int(day) for day in input_string.split(',')]}
            
    def _is_month(self, input_string):
        return any(month in input_string for month in _CALENDAR_MONTHS_ABBR)
            
    def _parse_month(self, input_string):
        input_string = input_string.replace(':', '') # match some actual cases in production
        if '-' in input_string:
            start_month, end_month = input_string.split('-')
            month_list = list(range(_CALENDAR_MONTHS_ABBR.index(start_month) + 1, _CALENDAR_MONTHS_ABBR.index(end_month) + 1))
        else:
            month_list = [_CALENDAR_MONTHS_ABBR.index(month) + 1 for month in input_string.split(',')]
        
        return {"bymonth": month_list}
                   
    def _is_year(self, input_string):
        return bool(re.match(r'^(\d{4})', input_string))
            
    def _parse_year(self, input_string):
        if '-' in input_string:
            start_year, end_year = [int(year) for year in input_string.split('-')]
        else:
            start_year = int(input_string)
            end_year = start_year
            
        return {"dtstart": datetime(start_year, 1, 1, tzinfo=timezone.utc), "until": datetime(end_year, 12, 31, tzinfo=timezone.utc)}
            
    def _parse_part(self, part):
        """
        Parse a part of the opening_hours string and return the corresponding kwargs to rrule constructor

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
            return {} # ignore those, the plugin doesn’t support time
        else:
            raise ValueError(f"Invalid part: {part}")
            
    def _parse_week_no(self, input_string):
        weeks = input_string.split('-')
        start_week = int(weeks[0])
        end_week = int(weeks[1].split('/')[0])
        interval = int(weeks[1].split('/')[1])
        return {"byweekno": list(range(start_week, end_week + 1, interval))}
    
    def _parse_regular(self, schedule):
        """
        Parse a regular schedule and return a rrule object.
            

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
            "2025 Jan,Apr,Jul,Oct Tu[1] 05:00-12:00"
            "2024-2025 Mo 05:00-12:00"
            "2024-2025 Dec: We[2,4] 09:00-19:00"
            "2024-2025 Sep-Nov We 09:00-19:00"
        """
        start_date = datetime.strptime(schedule['start_at'], '%Y-%m-%dT%H:%M:%S.%f%z') if schedule['start_at'] else None
        if schedule['end_at']:
            end_date = datetime.strptime(schedule['end_at'], '%Y-%m-%dT%H:%M:%S.%f%z')
        else:
            end_date = (datetime.now(timezone.utc) + timedelta(days=365))
            
        opening_hours = schedule['opening_hours']
            
        parts = opening_hours.split()
        kwargs = {
            "freq": MONTHLY,
            "dtstart": start_date,
            "until": end_date,
        }

        if parts[0] == 'week':
            kwargs["freq"] = WEEKLY
            kwargs.update(self._parse_week_no(parts[1]))            
            parts = parts[2:]

        for part in parts:
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
            for schedule in waste_data['schedules']:
                if schedule['schedule_type'] in ('regular', 'exception'):
                    my_rruleset.rrule(self._parse_regular(schedule))
                elif schedule['schedule_type'] in ('closed', 'closing_exception'):
                    my_rruleset.exrule(self._parse_closure(schedule))
            
            for entry in my_rruleset:
                entries.append(Collection(entry.date(), LABEL_MAP.get(waste_type), icon=ICON_MAP.get(waste_type)))

        return entries
