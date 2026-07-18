import datetime
import logging
from typing import TYPE_CHECKING, Any, Union, overload

from .waste_types import WasteType, display_name

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

    if TYPE_CHECKING:
        # The package exports the ``CollectionFactory`` callable as
        # ``Collection``. These TYPE_CHECKING-only overloads describe both the
        # call shapes that the factory accepts at runtime: the new-style
        # ``Collection(date=..., waste_type=...)`` and the legacy
        # ``Collection(date=..., t=..., icon=...)``. They affect type checking
        # only; the runtime ``__init__`` below is unchanged.
        @overload
        def __init__(self, date: datetime.date, waste_type: WasteType): ...

        @overload
        def __init__(
            self,
            date: datetime.date,
            t: str,
            icon: str | None = ...,
            picture: str | None = ...,
            location: str | None = ...,
            description: str | None = ...,
        ): ...

        def __init__(self, date: datetime.date, *args: Any, **kwargs: Any): ...

    else:

        def __init__(self, date: datetime.date, waste_type: WasteType):
            self._init_impl(date, waste_type)

    def _init_impl(self, date: datetime.date, waste_type: WasteType):
        self._date = date
        self._waste_type = waste_type
        self._type_override: str | None = None
        self._icon_override: str | None = None
        self._picture: str | None = None
        self._location: str | None = None
        self._description: str | None = None

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
        return self._type_override or display_name(self._waste_type)

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

    # Read-side Mapping protocol. The pre-refactor Collection subclassed ``dict``
    # ("to enable JSON serialization"), so ``dict(c)``, ``{**c}``, ``len(c)``,
    # iteration and ``c.items()/keys()/values()`` all worked — chiefly for
    # user-authored value/date templates that receive the collection as their
    # variable. This restores that surface over ``as_dict()`` without
    # reintroducing dict inheritance (which would clash with the custom
    # __eq__/__hash__). Note: ``json.dumps(c)`` still needs ``c.as_dict()`` — a
    # plain object is not JSON-encodable the way a dict subclass was.
    def keys(self):
        return self.as_dict().keys()

    def values(self):
        return self.as_dict().values()

    def items(self):
        return self.as_dict().items()

    def __iter__(self):
        return iter(self.as_dict())

    def __len__(self):
        return len(self.as_dict())

    @property
    def _identity_key(self) -> str:
        """Stable, locale-independent identity for equality and hashing.

        Uses the type override when one was set (legacy ``set_type``), else the
        canonical ``WasteType.id``. Deliberately NOT ``self.type`` (the display
        name), which follows the UI language, so two collections must not
        compare equal in one language and unequal in another.
        """
        return self._type_override or self._waste_type.id

    def __repr__(self):
        return f"Collection{{date={self.date}, waste_type={self._waste_type.id}}}"

    def __eq__(self, other):
        if not isinstance(other, Collection):
            return NotImplemented
        return self.date == other.date and self._identity_key == other._identity_key

    def __hash__(self):
        return hash((self.date, self._identity_key))


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

    # The package exports this factory instance as ``Collection`` for backward
    # compatibility. Existing sources annotate with ``Collection | None``, which
    # is evaluated at definition time, so the instance must support ``|`` like a
    # real class would. Delegate to the underlying Collection class.
    def __or__(self, other):
        return Union[Collection, other]  # noqa: UP007

    def __ror__(self, other):
        return Union[other, Collection]  # noqa: UP007


if TYPE_CHECKING:
    # At runtime ``CollectionFactory`` is a ``_CollectionMeta`` instance that
    # constructs the right Collection/LegacyCollection and supports
    # ``isinstance`` / ``|``. The package exports it as ``Collection``. Type
    # checkers need a real class so that both annotations (``list[Collection]``)
    # and the legacy constructor call (``Collection(date=..., t=..., icon=...)``)
    # type-check. ``Collection`` (below) carries a TYPE_CHECKING-only overload
    # accepting the legacy keyword arguments, so aliasing the factory to the
    # class is exact for the type checker.
    CollectionFactory = Collection
else:
    CollectionFactory = _CollectionMeta()


class CollectionGroup:
    """A group of collections on the same date (for calendar/sensor display)."""

    def __init__(self, date: datetime.date):
        self._date = date
        self._icon: str | None = None
        self._picture: str | None = None
        self._types: list[str] = []
        self._locations: list[str] = []
        self._descriptions: list[str] = []

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

    def __contains__(self, key):
        return key in self.as_dict()

    def get(self, key, default=None):
        return self.as_dict().get(key, default)

    # Read-side Mapping protocol, as on Collection (the pre-refactor
    # CollectionGroup also subclassed dict). Restores dict(g), {**g}, len(g),
    # iteration and g.items()/keys()/values() for templates.
    def keys(self):
        return self.as_dict().keys()

    def values(self):
        return self.as_dict().values()

    def items(self):
        return self.as_dict().items()

    def __iter__(self):
        return iter(self.as_dict())

    def __len__(self):
        return len(self.as_dict())

    def __repr__(self):
        return f"CollectionGroup{{date={self.date}, types={self.types}}}"


CollectionBase = Collection
