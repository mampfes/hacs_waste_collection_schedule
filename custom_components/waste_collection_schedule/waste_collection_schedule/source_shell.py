import datetime
import importlib
import logging
import traceback
from typing import Dict, Iterable, List, Optional, Protocol

from .collection import Collection

_LOGGER = logging.getLogger(__name__)


class Fetchable(Protocol):
    def fetch(self) -> list[Collection]:
        ...


class SourceModule(Protocol):
    TITLE: str
    DESCRIPTION: str
    URL: str

    Source: Fetchable


class Customize:
    """Customize one waste collection type."""

    def __init__(
        self,
        waste_type: str,
        alias: str | None = None,
        show: bool = True,
        icon: str | None = None,
        picture: str | None = None,
        use_dedicated_calendar: bool = False,
        dedicated_calendar_title: str | None = None,
    ):
        self._waste_type = waste_type
        self._alias = alias
        self._show = show
        self._icon = icon
        self._picture = picture
        self._use_dedicated_calendar = use_dedicated_calendar
        self._dedicated_calendar_title = dedicated_calendar_title

    @property
    def waste_type(self):
        return self._waste_type

    @property
    def alias(self):
        return self._alias

    @property
    def show(self):
        return self._show

    @property
    def icon(self):
        return self._icon

    @property
    def picture(self):
        return self._picture

    @property
    def use_dedicated_calendar(self):
        return self._use_dedicated_calendar

    @property
    def dedicated_calendar_title(self):
        return self._dedicated_calendar_title

    def __repr__(self):
        return f"Customize{{waste_type={self._waste_type}, alias={self._alias}, show={self._show}, icon={self._icon}, picture={self._picture}}}"


def filter_function(entry: Collection, customize: Dict[str, Customize]):
    c = customize.get(entry.type)
    if c is None:
        return True
    else:
        return c.show


def customize_function(entry: Collection, customize: Dict[str, Customize]):
    c = customize.get(entry.type)
    if c is not None:
        if c.alias is not None:
            entry.set_type(c.alias)
        if c.icon is not None:
            entry.set_icon(c.icon)
        if c.picture is not None:
            entry.set_picture(c.picture)
    return entry


def apply_day_offset(entry: Collection, day_offset: int) -> Collection:
    entry.set_date(entry.date + datetime.timedelta(days=day_offset))
    return entry


class SourceShell:
    def __init__(
        self,
        source: Fetchable,
        customize: Dict[str, Customize],
        title: str,
        description: str,
        url: Optional[str],
        calendar_title: Optional[str],
        unique_id: str,
        day_offset: int,
    ):
        self._source = source
        self._customize = customize
        self._title = title
        self._description = description
        self._url = url
        self._calendar_title = calendar_title
        self._unique_id = unique_id
        self._refreshtime: datetime.datetime | None = None
        self._entries: List[Collection] = []
        self._day_offset = day_offset

    @property
    def refreshtime(self):
        return self._refreshtime

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def url(self):
        return self._url

    @property
    def calendar_title(self):
        return self._calendar_title or self._title

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def day_offset(self):
        return self._day_offset

    def fetch(self) -> None:
        """Fetch data from source."""
        try:
            # fetch returns a list of Collection's
            entries: Iterable[Collection] = self._source.fetch()
        except Exception:
            _LOGGER.error(
                f"fetch failed for source {self._title}:\n{traceback.format_exc()}"
            )
            return
        self._refreshtime = datetime.datetime.now()

        # strip whitespaces
        for e in entries:
            e.set_type(e.type.strip())

        # filter hidden entries
        entries = filter(lambda x: filter_function(x, self._customize), entries)

        # customize fetched entries
        entries = map(lambda x: customize_function(x, self._customize), entries)

        # apply day offset
        if self._day_offset != 0:
            entries = map(lambda x: apply_day_offset(x, self._day_offset), entries)

        self._entries = list(entries)

    def get_dedicated_calendar_types(self) -> set[str]:
        """Return set of waste types with a dedicated calendar."""
        types = set()

        for key, customize in self._customize.items():
            if customize.show and customize.use_dedicated_calendar:
                types.add(key)

        return types

    def get_calendar_title_for_type(self, type: str) -> str:
        """Return calendar title for waste type (used for dedicated calendars)."""
        c = self._customize.get(type)
        if c is not None and c.dedicated_calendar_title:
            return c.dedicated_calendar_title

        return self.get_collection_type_name(type)

    def get_collection_type_name(self, type: str) -> str:
        c = self._customize.get(type)
        if c is not None and c.alias:
            return c.alias

        return type

    @staticmethod
    def create(
        source_name: str,
        customize: Dict[str, Customize],
        source_args,
        calendar_title: Optional[str] = None,
        day_offset: int = 0,
    ) -> "SourceShell | None":
        # load source module
        try:
            source_module: SourceModule = importlib.import_module(
                f"waste_collection_schedule.source.{source_name}"
            )
        except ImportError as e:
            if str(e).startswith(
                f"No module named 'waste_collection_schedule.source.{source_name}'"
            ):
                _LOGGER.error(f"source not found: {source_name}")
            else:
                _LOGGER.error(
                    f"error loading source {source_name}:\n{e} \n{traceback.format_exc()}"
                )
            return None

        # create source
        source: Fetchable = source_module.Source(**source_args)  # type: ignore

        # create source shell
        g = SourceShell(
            source=source,
            customize=customize,
            title=source_module.TITLE,
            description=source_module.DESCRIPTION,
            url=source_module.URL,
            calendar_title=calendar_title,
            unique_id=calc_unique_source_id(source_name, source_args),
            day_offset=day_offset,
        )

        return g


def calc_unique_source_id(source_name: str, source_args) -> str:
    return source_name + str(sorted(source_args.items()))
