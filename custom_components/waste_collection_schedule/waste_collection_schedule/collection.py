import datetime
from typing import Optional


class CollectionBase(dict):  # inherit from dict to enable JSON serialization
    def __init__(
        self,
        date: datetime.date,
        icon: Optional[str] = None,
        picture: Optional[str] = None,
    ):
        dict.__init__(self, date=date.isoformat(), icon=icon, picture=picture, start_hours_before=None, end_hours_after=None)
        self._date = date  # store date also as python date object

    @property
    def date(self):
        return self._date

    @property
    def daysTo(self):
        return (self._date - datetime.datetime.now().date()).days

    @property
    def icon(self):
        return self["icon"]

    def set_icon(self, icon: str):
        self["icon"] = icon

    @property
    def picture(self):
        return self["picture"]

    def set_picture(self, picture: str):
        self["picture"] = picture

    @property
    def start_hours_before(self):
        return self["start_hours_before"]

    def set_start_hours_before(self, hours: int):
        self["start_hours_before"] = int(hours)

    @property
    def end_hours_after(self):
        return self["end_hours_after"]

    def set_end_hours_after(self, hours: int):
        self["end_hours_after"] = int(hours)


class Collection(CollectionBase):
    def __init__(
        self,
        date: datetime.date,
        t: str,
        icon: Optional[str] = None,
        picture: Optional[str] = None,
    ):
        CollectionBase.__init__(self, date=date, icon=icon, picture=picture)
        self["type"] = t

    @property
    def type(self):
        return self["type"]

    def set_type(self, t: str):
        self["type"] = t

    def __repr__(self):
        return f"Collection{{date={self.date}, type={self.type}}}"


class CollectionGroup(CollectionBase):
    def __init__(self, date: datetime.date):
        CollectionBase.__init__(self, date=date)

    @staticmethod
    def create(group):
        """Create from list of Collection's."""
        x = CollectionGroup(group[0].date)
        if len(group) == 1:
            x.set_icon(group[0].icon)
            x.set_picture(group[0].picture)
        else:
            x.set_icon(f"mdi:numeric-{len(group)}-box-multiple")
        x["types"] = list(it.type for it in group)
        return x

    @property
    def types(self):
        return self["types"]

    def __repr__(self):
        return f"CollectionGroup{{date={self.date}, types={self.types}}}"
