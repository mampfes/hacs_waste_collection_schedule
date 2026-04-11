import datetime
from typing import Optional


class CollectionBase(dict):  # inherit from dict to enable JSON serialization
    def __init__(
        self,
        date: datetime.date,
        icon: Optional[str] = None,
        picture: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
    ):
        dict.__init__(self, date=date.isoformat(), icon=icon, picture=picture)
        self._date = date  # store date also as python date object

        loc = _clean_optional_str(location)
        if loc is not None:
            self["location"] = loc
        desc = _clean_optional_str(description)
        if desc is not None:
            self["description"] = desc

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
    def location(self):
        return self.get("location")

    @property
    def description(self):
        return self.get("description")

    def set_location(self, location: Optional[str]):
        loc = _clean_optional_str(location)
        if loc is None:
            self.pop("location", None)
        else:
            self["location"] = loc

    def set_description(self, description: Optional[str]):
        desc = _clean_optional_str(description)
        if desc is None:
            self.pop("description", None)
        else:
            self["description"] = desc

    def set_date(self, date: datetime.date):
        self._date = date
        self["date"] = date.isoformat()


def _clean_optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    return stripped or None


class Collection(CollectionBase):
    def __init__(
        self,
        date: datetime.date,
        t: str,
        icon: Optional[str] = None,
        picture: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
    ):
        CollectionBase.__init__(
            self,
            date=date,
            icon=icon,
            picture=picture,
            location=location,
            description=description,
        )
        self["type"] = t

    @property
    def type(self) -> str:
        return self["type"]

    def set_type(self, t: str):
        self["type"] = t

    def __repr__(self):
        return f"Collection{{date={self.date}, type={self.type}}}"


class CollectionGroup(CollectionBase):
    def __init__(self, date: datetime.date):
        CollectionBase.__init__(self, date=date)

    @staticmethod
    def create(group: list[Collection]):
        """Create from list of Collection's."""
        x = CollectionGroup(group[0].date)
        if len(group) == 1:
            x.set_icon(group[0].icon)
            x.set_picture(group[0].picture)
        else:
            x.set_icon(f"mdi:numeric-{len(group)}-box-multiple")
        x["types"] = list(it.type for it in group)

        ordered_locs: list[str] = []
        for it in group:
            loc = it.get("location")
            if isinstance(loc, str) and loc.strip():
                ordered_locs.append(loc.strip())
        unique_locs = list(dict.fromkeys(ordered_locs))
        if unique_locs:
            x["locations"] = unique_locs
            x["location"] = ", ".join(unique_locs)

        ordered_descs: list[str] = []
        for it in group:
            desc = it.get("description")
            if isinstance(desc, str) and desc.strip():
                ordered_descs.append(desc.strip())
        unique_descs = list(dict.fromkeys(ordered_descs))
        if unique_descs:
            x["descriptions"] = unique_descs
            x["description"] = ", ".join(unique_descs)

        return x

    @property
    def types(self) -> list[str]:
        return self["types"]

    @property
    def locations(self):
        return self.get("locations")

    @property
    def descriptions(self):
        return self.get("descriptions")

    def __repr__(self):
        return f"CollectionGroup{{date={self.date}, types={self.types}}}"
