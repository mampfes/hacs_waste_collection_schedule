import calendar
import unicodedata
from datetime import date, timedelta

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Technické služby Český Brod"
DESCRIPTION = "Source for waste collection in Český Brod"
URL = "https://www.tsceskybrod.cz/"

TEST_CASES = {
    "Monday": {"street": "nám. Arnošta z Pardubic"},
    "Tuesday": {"street": "Klučovská"},
    "Wednesday_no_accent_characters": {"street": "Jiriho Wolkera"},
    "Wednesday": {"street": "Ke Spravedlnosti"},
    "Friday": {"street": "Prokopa Velikého"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit [https://www.tsceskybrod.cz/pravidelny-svoz-odpadu](https://www.tsceskybrod.cz/pravidelny-svoz-odpadu) and enter the street or location name exactly as listed in the table.",
}

street_groups = {
    calendar.MONDAY: ["nám. Arnošta z Pardubic", "Husovo nám.", "Tyršova", "Komenského", "Žitomířská", "Želivského", "Žižkova", "Štolmířská", "Na Vyhlídce", "Miškovského", "Masarykova", "5. května", "Vítězná", "Sokolovská", "Kollárova", "Pernerova", "Krále Jiřího - od křižovatky ZZN směr nádraží", "Maroldova", "Mozartova", "Smetanova", "Na Louži", "Jana Koziny", "Na Vanderkách"],
    calendar.TUESDAY: ["Klučovská", "Bulharská", "Ruská", "Moravská", "Jugoslávská", "Pod Velkým Vrchem", "Slezská", "Za Svitávkou", "Slovenská", "Marie Majerové", "Lužická", "Zborovská", "Za Pilou", "Kounická", "Pod Hájem", "Sportovní", "Krále Jiřího od křižovatky ZZN směr náměstí", "V Chobotě", "Tovární", "Polomská", "Pod Malým Vrchem", "V Lukách", "Na Prutě", "Na Křemínku", "V Lánech", "U Drahy", "Císaře Zikmunda", "Na Blatech", "Ke Zvonečku", "Lomená"],
    calendar.WEDNESDAY: ["Jiřího Wolkera", "Ke Spravedlnosti", "Trstenická", "Mikoláše Alše", "Zárubova", "28.října", "U Garáží", "Lukavského", "Františka Macháčka", "U Studánky", "Za Nemocnicí", "Krátká", "Boženy Němcové", "Svatopluka Čecha", "Bezručova", "Suvorovova", "Palackého", "Na Cihelně", "Rokycanova", "Roháčova", "Fugnerova", "Nábřežní", "Jeronýmova", "Tuchorazská", "K Dolánkám", "Na Bělidle", "Sokolská"],
    # No residual municipal waste and bio waste collection on Thursday
    calendar.FRIDAY: ["Prokopa Velikého", "Podskalí", "Sadová", "Havlíčkova", "Jungmannova", "Lázeňská", "Hřbitovní", "Jana Kouly", "Šafaříkova", "Jateční", "Jatecká", "Liblice", "Štolmíř", "Zahrady"]
}

def normalize_string(s):
    """Remove accents from a string for case-insensitive and accent-insensitive comparison"""
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower()

# Create a lookup dictionary for street-to-weekday mapping (without accents)
street_collection_weekdays = {
    normalize_string(street): weekday
    for weekday, streets in street_groups.items()
    for street in streets
}

def get_collection_weekday(street):
    """Return the waste collection weekday for a given street (ignoring accents)"""
    return street_collection_weekdays.get(normalize_string(street), -1)

def is_street_in_collection(street):
    """Check if a street exists in the collection schedule (ignoring accents)"""
    return normalize_string(street) in street_collection_weekdays

class Source:
    def __init__(self, street):
        self._street = street

    def fetch(self):
        if not is_street_in_collection(self._street):
            raise SourceArgumentException("street", f"Street '{self._street}' not found")

        start_date = date(2025, 1, 1)
        end_date = date(2027, 12, 31)
        current_date = start_date
        collection_weekday = get_collection_weekday(self._street)

        entries = []

        while current_date <= end_date:
            year, week, _ = current_date.isocalendar()
            month = current_date.month

            even_week = week % 2 == 0
            odd_week = not even_week
            
            # Residual municipal waste and bio waste are only collected on weekdays based on location
            if current_date.weekday() == collection_weekday:
                # Residual municipal waste collected every odd week
                if odd_week:
                    entries.append(Collection(current_date, "Zbytkový komunální odpad", icon="mdi:trash-can"))

                if (
                        # Bio waste collected every week from April to November
                        (4 <= month <= 11) or
                        # Bio waste collected every even week in March
                        (month == 3 and even_week) or
                        # Bio waste collected every first even week in month (from December to March)
                        (even_week and current_date.day <= 14)
                    ):
                    entries.append(Collection(current_date, "Biologický odpad", icon="mdi:leaf"))

            # Paper waste is collected every odd week on Wednesday
            if current_date.weekday() == calendar.WEDNESDAY and odd_week:
                entries.append(Collection(current_date, "Papír a lepenka", icon="mdi:package-variant"))

            # Plastic waste is collected every even week on Thursday
            if current_date.weekday() == calendar.THURSDAY and even_week:
                entries.append(Collection(current_date, "Plasty", icon="mdi:recycle"))
            
            current_date += timedelta(days=1)

        return entries
