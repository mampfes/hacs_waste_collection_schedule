from datetime import date, timedelta

import datetime

def _daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

class Source:
    def __init__(self, **kwargs):
        pass

    def fetch(self):
        today = date.today()
        year = today.year

        entries = []

        # -------------------------
        #  Ordures ménagères (rouge)
        #  Tri sélectif (jaune)
        #  → Tous les vendredis
        # -------------------------
        for single_date in _daterange(date(year, 1, 1), date(year, 12, 31)):
            if single_date.weekday() == 4:  # Vendredi
                entries.append(
                    {
                        "date": single_date,
                        "type": "Ordures ménagères (rouge)",
                    }
                )
                entries.append(
                    {
                        "date": single_date,
                        "type": "Tri sélectif (jaune)",
                    }
                )

        # -------------------------
        #  Déchets verts
        #  → Tous les mercredis, 1 semaine sur 2
        #  → De début mars à fin novembre
        # -------------------------
        start_green = date(year, 3, 1)
        end_green = date(year, 11, 30)

        # Trouver le premier mercredi
        first_wed = start_green + timedelta((2 - start_green.weekday()) % 7)

        # Semaine alternée → toutes les 2 semaines
        current = first_wed
        week_toggle = False  # permet de commencer correctement

        while current <= end_green:
            entries.append(
                {
                    "date": current,
                    "type": "Déchets verts",
                }
            )
            current += timedelta(days=14)

        return entries
