import datetime
import importlib
import logging
import traceback
from typing import Dict, List, Optional

from .collection import Collection

_LOGGER = logging.getLogger(__name__)


class Customize:
    """Customize one waste collection type."""

    def __init__(
        self,
        waste_type,
        alias=None,
        show=True,
        icon=None,
        picture=None,
        use_dedicated_calendar=False,
        dedicated_calendar_title=None,
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


class SourceShell:
    def __init__(
        self,
        source,
        customize: Dict[str, Customize],
        title: str,
        description: str,
        url: Optional[str],
        calendar_title: Optional[str],
        unique_id: str,
    ):
        self._source = source
        self._customize = customize
        self._title = title
        self._description = description
        self._url = url
        self._calendar_title = calendar_title
        self._unique_id = unique_id
        self._refreshtime = None
        self._entries: List[Collection] = []

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

    def fetch(self):
        """Fetch data from source."""
        try:
            # fetch returns a list of Collection's
            entries = self._source.fetch()
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

        self._entries = list(entries)

    def get_dedicated_calendar_types(self):
        """Return set of waste types with a dedicated calendar."""
        types = set()

        for key, customize in self._customize.items():
            if customize.show and customize.use_dedicated_calendar:
                types.add(key)

        return types

    def get_calendar_title_for_type(self, type):
        """Return calendar title for waste type (used for dedicated calendars)."""
        c = self._customize.get(type)
        if c is not None and c.dedicated_calendar_title:
            return c.dedicated_calendar_title

        return self.get_collection_type_name(type)

    def get_collection_type_name(self, type):
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
    ):
        # load source module
        try:
            source_module = importlib.import_module(
                f"waste_collection_schedule.source.{source_name}"
            )
        except ImportError:
            _LOGGER.error(f"source not found: {source_name}")
            return

        # create source
        source = source_module.Source(**source_args)  # type: ignore

        # create source shell
        g = SourceShell(
            source=source,
            customize=customize,
            title=source_module.TITLE,  # type: ignore[attr-defined]
            description=source_module.DESCRIPTION,  # type: ignore[attr-defined]
            url=source_module.URL,  # type: ignore[attr-defined]
            calendar_title=calendar_title,
            unique_id=calc_unique_source_id(source_name, source_args),
        )

        return g


def calc_unique_source_id(source_name, source_args):
    return source_name + str(sorted(source_args.items()))
