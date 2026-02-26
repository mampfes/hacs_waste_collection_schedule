import datetime
import logging

from waste_collection_schedule import Collection

TITLE = "ZGK Oborniki Śląskie (Alba)"
DESCRIPTION = "Source for waste collection schedule in Oborniki Śląskie, Poland. Uses static data from official schedules."
URL = "https://www.oborniki-slaskie.pl"
TEST_CASES = {
    "Zajączków": {
        "street": "Zajączków",
    },
}
ICON_MAP = {
    "Odpady zmieszane": "mdi:trash-can",
    "Papier": "mdi:newspaper-variant-outline",
    "Metale i tworzywa sztuczne": "mdi:bottle-soda-classic-outline",
    "Szkło": "mdi:glass-fragile",
    "Bioodpady": "mdi:recycle",
}
_LOGGER = logging.getLogger(__name__)

# Funkcja pomocnicza dla skrócenia zapisu
def d(month, day):
    return datetime.date(2026, month, day)

# Funkcja budująca chronologiczną listę dla każdej lokalizacji
def build(zmieszane, plastik, makulatura, szklo):
    res = [(dt, "Odpady zmieszane") for dt in zmieszane]
    res += [(dt, "Plastik") for dt in plastik]
    res += [(dt, "Makulatura") for dt in makulatura]
    res += [(dt, "Szkło") for dt in szklo]
    # Sortowanie datami od najwcześniejszej
    return sorted(res, key=lambda x: x[0])

# --- 1. DATY ODPADÓW SELEKTYWNYCH (Obraz 1) ---
# Grupa Poniedziałek (Borkowice, Siemianice, Wilczyn, Oborniki: Wolności, Rycerska)
S1_P = [d(1,12), d(1,26), d(2,9), d(2,23), d(3,9), d(3,23), d(4,4), d(4,20), d(5,4), d(5,18), d(6,1), d(6,15), d(6,29), d(7,13), d(7,27), d(8,10), d(8,24), d(9,7), d(9,21), d(10,5), d(10,19), d(11,2), d(11,16), d(11,30), d(12,14), d(12,28)]
S1_M = [d(1,19), d(2,16), d(3,16), d(4,13), d(5,11), d(6,8), d(7,6), d(8,3), d(8,31), d(9,28), d(10,26), d(11,23), d(12,21)]
S1_S = [d(1,5), d(2,2), d(3,2), d(3,30), d(4,27), d(5,25), d(6,22), d(7,20), d(8,17), d(9,14), d(10,12), d(11,9), d(12,7)]

# Grupa Wtorek (Jary, Kotowice, Kuraszków, Lubnów, Nowosielce, Paniowice, Raków, Rościsławice, Uraz, Oborniki: Ciechołowicka, Komuny Paryskiej, Ułańska, Cicha, Tulipanowa)
S2_P = [d(1,13), d(1,27), d(2,10), d(2,24), d(3,10), d(3,24), d(4,7), d(4,21), d(5,5), d(5,19), d(6,2), d(6,16), d(6,30), d(7,14), d(7,28), d(8,11), d(8,25), d(9,8), d(9,22), d(10,6), d(10,20), d(11,3), d(11,17), d(12,1), d(12,15), d(12,29)]
S2_M = [d(1,20), d(2,17), d(3,17), d(4,14), d(5,12), d(6,9), d(7,7), d(8,4), d(9,1), d(9,29), d(10,27), d(11,24), d(12,22)]
S2_S = [d(1,10), d(2,3), d(3,3), d(3,31), d(4,28), d(5,26), d(6,23), d(7,21), d(8,18), d(9,15), d(10,13), d(11,10), d(12,8)]

# Grupa Środa (Bagno, Brzeźno Małe, Morzęcin Mały, Osola, Osolin, Wielka Lipa)
S3_P = [d(1,14), d(1,28), d(2,11), d(2,25), d(3,11), d(3,25), d(4,8), d(4,22), d(5,6), d(5,20), d(6,3), d(6,17), d(7,1), d(7,15), d(7,29), d(8,12), d(8,26), d(9,9), d(9,23), d(10,7), d(10,21), d(11,4), d(11,18), d(12,2), d(12,16), d(12,30)]
S3_M = [d(1,21), d(2,18), d(3,18), d(4,15), d(5,13), d(6,10), d(7,8), d(8,5), d(9,2), d(9,30), d(10,28), d(11,25), d(12,23)]
S3_S = [d(1,7), d(2,4), d(3,4), d(4,1), d(4,29), d(5,27), d(6,24), d(7,22), d(8,19), d(9,16), d(10,14), d(11,14), d(12,9)]

# Grupa Czwartek (Pęgów, Zajączków)
S4_P = [d(1,3), d(1,15), d(1,29), d(2,12), d(2,26), d(3,12), d(3,26), d(4,9), d(4,23), d(5,7), d(5,21), d(6,6), d(6,18), d(7,2), d(7,16), d(7,30), d(8,13), d(8,27), d(9,10), d(9,24), d(10,8), d(10,22), d(11,5), d(11,19), d(12,3), d(12,17), d(12,31)]
S4_M = [d(1,22), d(2,19), d(3,19), d(4,16), d(5,14), d(6,11), d(7,9), d(8,6), d(9,3), d(10,1), d(10,29), d(11,26), d(12,12)]
S4_S = [d(1,8), d(2,5), d(3,5), d(4,2), d(4,30), d(5,28), d(6,25), d(7,23), d(8,20), d(9,17), d(10,15), d(11,12), d(12,10)]

# Grupa Piątek (Oborniki Śląskie - reszta ulic)
S5_P = [d(1,2), d(1,16), d(1,30), d(2,13), d(2,27), d(3,13), d(3,27), d(4,10), d(4,24), d(5,8), d(5,22), d(6,5), d(6,19), d(7,3), d(7,17), d(7,31), d(8,14), d(8,28), d(9,11), d(9,25), d(10,9), d(10,23), d(11,6), d(11,20), d(12,4), d(12,18)]
S5_M = [d(1,23), d(2,20), d(3,20), d(4,17), d(5,15), d(6,12), d(7,10), d(8,7), d(9,4), d(10,2), d(10,30), d(11,27), d(12,19)]
S5_S = [d(1,9), d(2,6), d(3,6), d(3,3), d(5,2), d(6,26), d(7,24), d(8,21), d(9,18), d(10,16), d(11,13), d(12,11)]

# --- 2. DATY ODPADÓW ZMIESZANYCH (Obraz 2) ---
Z_BAGNO_OSOLIN = [d(1,5), d(1,19), d(2,2), d(2,16), d(3,2), d(3,16), d(3,30), d(4,13), d(4,27), d(5,11), d(5,25), d(6,8), d(6,22), d(7,6), d(7,20), d(8,3), d(8,17), d(8,31), d(9,14), d(9,28), d(10,12), d(10,26), d(11,9), d(11,23), d(12,7), d(12,21)]
Z_BRZEZNO_OSOLA = [d(1,7), d(1,20), d(2,3), d(2,17), d(3,3), d(3,17), d(3,31), d(4,14), d(4,28), d(5,12), d(5,26), d(6,9), d(6,23), d(7,7), d(7,21), d(8,4), d(8,18), d(9,1), d(9,15), d(9,29), d(10,13), d(10,27), d(11,10), d(11,24), d(12,8), d(12,22)]
Z_JARY_ROSCISLAWICE = [d(1,7), d(1,21), d(2,4), d(2,18), d(3,4), d(3,18), d(4,1), d(4,15), d(5,13), d(5,27), d(6,10), d(6,24), d(7,8), d(7,22), d(8,5), d(8,19), d(9,2), d(9,16), d(10,14), d(10,28), d(11,12), d(11,25), d(12,9), d(12,23)]
Z_KURASZKOW_SIEMIANICE = [d(1,8), d(1,22), d(2,5), d(2,19), d(3,5), d(3,19), d(4,2), d(4,16), d(4,30), d(5,14), d(5,28), d(6,11), d(6,25), d(7,9), d(7,23), d(8,6), d(8,20), d(9,3), d(9,17), d(10,1), d(10,15), d(10,29), d(11,12), d(11,26), d(12,10), d(12,19)]
Z_BORKOWICE_KOWALE = [d(1,9), d(1,23), d(2,6), d(2,20), d(3,6), d(3,20), d(4,3), d(4,17), d(5,2), d(5,15), d(5,29), d(6,12), d(6,26), d(7,10), d(7,24), d(8,7), d(8,21), d(9,4), d(9,18), d(10,2), d(10,16), d(10,30), d(11,13), d(11,27), d(11,11), d(11,12), d(12,19)]
Z_PEGOW_A = [d(1,12), d(1,26), d(2,9), d(2,23), d(3,9), d(3,23), d(4,11), d(4,20), d(5,4), d(5,18), d(6,1), d(6,15), d(6,29), d(7,13), d(7,27), d(8,10), d(8,24), d(9,7), d(9,21), d(10,5), d(10,19), d(11,2), d(11,16), d(11,30), d(12,14), d(12,28)]
Z_PEGOW_B = [d(1,13), d(1,27), d(2,10), d(2,24), d(3,10), d(3,24), d(4,7), d(4,21), d(5,5), d(5,19), d(6,2), d(6,16), d(6,30), d(7,14), d(7,28), d(8,11), d(8,25), d(9,8), d(9,22), d(10,6), d(10,20), d(11,3), d(11,17), d(12,1), d(12,15), d(12,29)]
Z_KOTOWICE_ZAJACZKOW = [d(1,14), d(1,28), d(2,11), d(2,25), d(3,11), d(3,25), d(4,8), d(4,22), d(5,6), d(5,20), d(6,3), d(6,17), d(7,1), d(7,15), d(7,29), d(8,12), d(8,26), d(9,9), d(9,23), d(10,7), d(10,21), d(11,4), d(11,18), d(12,2), d(12,16), d(12,30)]
Z_KOLONIA_RAKOW = [d(1,2), d(1,15), d(1,29), d(2,12), d(2,26), d(3,12), d(3,26), d(4,9), d(4,23), d(5,7), d(5,21), d(6,5), d(6,18), d(7,2), d(7,16), d(7,30), d(8,13), d(8,27), d(9,10), d(9,24), d(10,8), d(10,22), d(11,5), d(11,19), d(12,3), d(12,17), d(12,31)]
Z_URAZ = [d(1,2), d(1,16), d(1,30), d(2,13), d(2,27), d(3,13), d(3,27), d(4,10), d(4,24), d(5,8), d(5,22), d(6,5), d(6,19), d(7,3), d(7,17), d(7,31), d(8,14), d(8,28), d(9,11), d(9,25), d(10,9), d(10,23), d(11,6), d(11,20), d(12,4), d(12,18)]

# --- 3. HARMONOGRAM OSTATECZNY ---
HARMONOGRAM_ODPADÓW = {
    # Bagno, Osolin i okolice
    "Bagno": build(Z_BAGNO_OSOLIN, S3_P, S3_M, S3_S),
    "Osolin": build(Z_BAGNO_OSOLIN, S3_P, S3_M, S3_S),
    "Osolin ul. Wyszyńskiego": build(Z_BRZEZNO_OSOLA, S3_P, S3_M, S3_S),
    "Osola": build(Z_BRZEZNO_OSOLA, S3_P, S3_M, S3_S),
    "Brzeźno Małe": build(Z_BRZEZNO_OSOLA, S3_P, S3_M, S3_S),
    "Wielka Lipa": build(Z_BRZEZNO_OSOLA, S3_P, S3_M, S3_S),
    "Morzęcin Mały": build(Z_BRZEZNO_OSOLA, S3_P, S3_M, S3_S),

    # Pęgów i Zajączków
    "Pęgów A (Prawa strona do Wrocławia)": build(Z_PEGOW_A, S4_P, S4_M, S4_S),
    "Pęgów B (Lewa strona do Wrocławia)": build(Z_PEGOW_B, S4_P, S4_M, S4_S),
    "Pęgów ul. Ogrodowa (2, 4, 8, 12)": build(Z_KOTOWICE_ZAJACZKOW, S4_P, S4_M, S4_S),
    "Zajączków": build(Z_KOTOWICE_ZAJACZKOW, S4_P, S4_M, S4_S),

    # Oborniki Śląskie (Podział na ulice)
    "Oborniki Śląskie ul. Wolności, Rycerska": build(Z_BORKOWICE_KOWALE, S1_P, S1_M, S1_S),
    "Oborniki Śląskie ul. Ciechołowicka, Komuny Paryskiej, Ułańska, Cicha, Tulipanowa": build(Z_JARY_ROSCISLAWICE, S2_P, S2_M, S2_S),
    "Oborniki Śląskie (Pozostałe ulice)": build(Z_BORKOWICE_KOWALE, S5_P, S5_M, S5_S),

    # Inne wioski
    "Uraz": build(Z_URAZ, S2_P, S2_M, S2_S),
    "Jary": build(Z_JARY_ROSCISLAWICE, S2_P, S2_M, S2_S),
    "Rościsławice": build(Z_JARY_ROSCISLAWICE, S2_P, S2_M, S2_S),
    "Morzęcin Wielki": build(Z_JARY_ROSCISLAWICE, S2_P, S2_M, S2_S),
    "Siemianice": build(Z_KURASZKOW_SIEMIANICE, S1_P, S1_M, S1_S),
    "Kuraszków": build(Z_KURASZKOW_SIEMIANICE, S2_P, S2_M, S2_S),
    "Wilczyn": build(Z_BORKOWICE_KOWALE, S1_P, S1_M, S1_S),
    "Borkowice": build(Z_BORKOWICE_KOWALE, S1_P, S1_M, S1_S),
    "Kowale": build(Z_BORKOWICE_KOWALE, S1_P, S1_M, S1_S),
    "Piekary": build(Z_BORKOWICE_KOWALE, S1_P, S1_M, S1_S),
    "Przecławice": build(Z_BORKOWICE_KOWALE, S1_P, S1_M, S1_S),
    "Golędzinów": build(Z_BORKOWICE_KOWALE, S2_P, S2_M, S2_S),
    "Kolonia Golędzinów": build(Z_KOLONIA_RAKOW, S2_P, S2_M, S2_S),
    "Lubnów": build(Z_KOLONIA_RAKOW, S2_P, S2_M, S2_S),
    "Raków": build(Z_KOLONIA_RAKOW, S2_P, S2_M, S2_S),
    "Niziny": build(Z_KOLONIA_RAKOW, S2_P, S2_M, S2_S),
    "Nowosielce": build(Z_KOLONIA_RAKOW, S2_P, S2_M, S2_S),
    "Kotowice": build(Z_KOTOWICE_ZAJACZKOW, S2_P, S2_M, S2_S),
    "Paniowice": build(Z_KOTOWICE_ZAJACZKOW, S2_P, S2_M, S2_S)
}

class Source:
    def __init__(self, street: str = None):
        self._street = street

    def fetch(self) -> list[Collection]:
        """Fetch waste collection data using static constants."""
        entries = []
        
        if not self._street:
            _LOGGER.warning("Street name not provided")
            return entries
        
        if self._street not in HARMONOGRAM_ODPADÓW:
            _LOGGER.warning(f"Street '{self._street}' not found in schedule")
            return entries
        
        # Get the schedule for the specified street
        schedule = HARMONOGRAM_ODPADÓW[self._street]
        
        # Convert tuples to Collection objects
        for date, waste_type in schedule:
            entries.append(
                Collection(
                    date,
                    waste_type,
                    ICON_MAP.get(waste_type, "mdi:recycle")
                )
            )
        
        return entries
