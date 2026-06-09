import datetime
import logging
from typing import Optional

from .waste_types import WasteType

_LOGGER = logging.getLogger(__name__)


def _clean_optional_str(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    return stripped or None


class Collection:
    """A single waste collection event: (date, WasteType).

    New-style (preferred): Collection(date=..., waste_type=GENERAL_WASTE)
    Sources using BaseSource return these directly.
    """

    def __init__(self, date: datetime.date, waste_type: WasteType):
        self._date = date
        self._waste_type = waste_type
        self._type_override = None
        self._icon_override = None
        self._picture = None
        self._location = None
        self._description = None

    @property
    def date(self) -> datetime.date:
        return self._date

    @property
    def daysTo(self) -> int:
        return (self._date - datetime.datetime.now().date()).days

    @property
    def waste_type(self) -> WasteType:
        return self._waste_type

    @property
    def type(self) -> str:
        return self._type_override or self._waste_type.names.get(
            "en", self._waste_type.id
        )

    @property
    def icon(self) -> str:
        return self._icon_override or self._waste_type.icon

    @property
    def picture(self):
        return self._picture

    @property
    def location(self):
        return self._location

    @property
    def description(self):
        return self._description

    def set_type(self, t: str):
        self._type_override = t

    def set_icon(self, icon: str):
        self._icon_override = icon

    def set_picture(self, picture: str):
        self._picture = picture

    def set_date(self, date: datetime.date):
        self._date = date

    def set_location(self, location):
        self._location = _clean_optional_str(location)

    def set_description(self, description):
        self._description = _clean_optional_str(description)

    def as_dict(self) -> dict:
        d = {
            "date": self._date.isoformat(),
            "type": self.type,
            "icon": self.icon,
            "picture": self.picture,
        }
        if self._location is not None:
            d["location"] = self._location
        if self._description is not None:
            d["description"] = self._description
        return d

    def __getitem__(self, key):
        return self.as_dict()[key]

    def __setitem__(self, key, value):
        if key == "type":
            self.set_type(value)
        elif key == "icon":
            self.set_icon(value)
        elif key == "picture":
            self.set_picture(value)
        elif key == "date":
            self._date = (
                datetime.date.fromisoformat(value) if isinstance(value, str) else value
            )
        elif key == "location":
            self.set_location(value)
        elif key == "description":
            self.set_description(value)

    def __contains__(self, key):
        return key in self.as_dict()

    def get(self, key, default=None):
        return self.as_dict().get(key, default)

    def update(self, d: dict):
        for k, v in d.items():
            self[k] = v

    def __repr__(self):
        return f"Collection{{date={self.date}, waste_type={self._waste_type.id}}}"

    def __eq__(self, other):
        if not isinstance(other, Collection):
            return NotImplemented
        return self.date == other.date and self.type == other.type

    def __hash__(self):
        return hash((self.date, self.type))


class LegacyCollection(Collection):
    """Adapter for old-style sources that pass t= and icon= strings."""

    def __init__(
        self,
        date: datetime.date,
        t: str,
        icon=None,
        picture=None,
        location=None,
        description=None,
    ):
        from .waste_types import OTHER

        ad_hoc = WasteType(
            id=f"legacy_{t}",
            icon=icon or OTHER.icon,
            color=OTHER.color,
            names={"en": t},
        )
        super().__init__(date=date, waste_type=ad_hoc)
        self._picture = picture
        self._location = _clean_optional_str(location)
        self._description = _clean_optional_str(description)


def _collection_factory(
    date: datetime.date,
    t=None,
    icon=None,
    picture=None,
    location=None,
    description=None,
    waste_type=None,
) -> Collection:
    if waste_type is not None:
        c = Collection(date=date, waste_type=waste_type)
        if picture is not None:
            c.set_picture(picture)
        if location is not None:
            c.set_location(location)
        if description is not None:
            c.set_description(description)
        return c
    if t is not None:
        return LegacyCollection(
            date=date,
            t=t,
            icon=icon,
            picture=picture,
            location=location,
            description=description,
        )
    raise ValueError("Collection requires either waste_type or t parameter")


class _CollectionMeta:
    def __call__(self, *args, **kwargs):
        return _collection_factory(*args, **kwargs)

    def __instancecheck__(self, instance):
        return isinstance(instance, Collection)

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, Collection)


CollectionFactory = _CollectionMeta()


class CollectionGroup:
    """A group of collections on the same date (for calendar/sensor display)."""

    def __init__(self, date: datetime.date):
        self._date = date
        self._icon = None
        self._picture = None
        self._types = []
        self._locations = []
        self._descriptions = []

    @staticmethod
    def create(group):
        x = CollectionGroup(group[0].date)
        if len(group) == 1:
            x._icon = group[0].icon
            x._picture = group[0].picture
        else:
            x._icon = f"mdi:numeric-{len(group)}-box-multiple"
        x._types = [it.type for it in group]

        ordered_locs = [
            it.location.strip()
            for it in group
            if isinstance(it.location, str) and it.location.strip()
        ]
        x._locations = list(dict.fromkeys(ordered_locs))

        ordered_descs = [
            it.description.strip()
            for it in group
            if isinstance(it.description, str) and it.description.strip()
        ]
        x._descriptions = list(dict.fromkeys(ordered_descs))

        return x

    @property
    def date(self) -> datetime.date:
        return self._date

    @property
    def daysTo(self) -> int:
        return (self._date - datetime.datetime.now().date()).days

    @property
    def icon(self):
        return self._icon

    @property
    def picture(self):
        return self._picture

    @property
    def types(self) -> list:
        return self._types

    @property
    def locations(self):
        return self._locations or None

    @property
    def location(self):
        return ", ".join(self._locations) if self._locations else None

    @property
    def descriptions(self):
        return self._descriptions or None

    @property
    def description(self):
        return ", ".join(self._descriptions) if self._descriptions else None

    def as_dict(self) -> dict:
        d = {
            "date": self._date.isoformat(),
            "icon": self._icon,
            "picture": self._picture,
            "types": self._types,
        }
        if self._locations:
            d["locations"] = self._locations
            d["location"] = ", ".join(self._locations)
        if self._descriptions:
            d["descriptions"] = self._descriptions
            d["description"] = ", ".join(self._descriptions)
        return d

    def __getitem__(self, key):
        return self.as_dict()[key]

    def get(self, key, default=None):
        return self.as_dict().get(key, default)

    def __repr__(self):
        return f"CollectionGroup{{date={self.date}, types={self.types}}}"


CollectionBase = Collection
