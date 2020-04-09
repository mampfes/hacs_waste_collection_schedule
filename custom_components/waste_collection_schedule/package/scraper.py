#!/usr/bin/python3

from itertools import islice
import logging
import collections
import os
import datetime
import importlib
import itertools

from .helpers import CollectionAppointment, CollectionAppointmentGroup

_LOGGER = logging.getLogger(__name__)


class Customize:
    """Customize one waste collection type."""

    def __init__(self, name, alias=None, show=True, icon=None, picture=None):
        self._name = name
        self._alias = alias
        self._show = show
        self._icon = icon
        self._picture = picture

    @property
    def name(self):
        return self._name

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

    def __repr__(self):
        return f"Customize{{name={self.name}, alias={self.alias}, show={self.show}, icon={self.icon}, picture={self.picture}}}"


def filter_function(entry: CollectionAppointment, customize: {}):
    c = customize.get(entry.type)
    if c is None:
        return True
    else:
        return c.show


def customize_function(entry: CollectionAppointment, customize: {}):
    c = customize.get(entry.type)
    if c is not None:
        if c.alias is not None:
            entry.set_type(c.alias)
        if c.icon is not None:
            entry.set_icon(c.icon)
        if c.picture is not None:
            entry.set_picture(c.picture)
    return entry


class Scraper:
    def __init__(self, source: str, customize: {}):
        self._source = source
        self._entries = []  # list of entries of type CollectionAppointment
        self._refreshtime = None
        self._customize = customize  # dict of class Customize

    @property
    def source(self):
        return self._source

    @property
    def refreshtime(self):
        return self._refreshtime

    def fetch(self):
        """Fetch data from source."""
        try:
            # fetch returns a list of CollectionAppointment's
            entries = self._source.fetch()
            self._refreshtime = datetime.datetime.now()
        except Exception as error:
            _LOGGER.error(f"fetch failed for source {self._source}: {error}")

        # filter hidden entries
        entries = filter(lambda x: filter_function(x, self._customize), entries)

        # customize fetched entries
        entries = map(lambda x: customize_function(x, self._customize), entries)

        self._entries = list(entries)

    def get_types(self):
        """Return set() of all appointment types."""
        types = set()
        for e in self._entries:
            types.add(e.type)
        return types

    def get_upcoming(self, count=None, leadtime=None, types=None, include_today=False):
        """Return list of all entries, limited by count and/or leadtime.
        
        Keyword arguments:
        count -- limits the number of returned entries (default=10)
        leadtime -- limits the timespan in days of returned entries (default=7, 0 = today)
        """
        return self._filter(
            self._entries,
            count=count,
            leadtime=leadtime,
            types=types,
            include_today=include_today,
        )

    def get_upcoming_group_by_day(
        self, count=None, leadtime=None, types=None, include_today=False
    ):
        """Return list of all entries, grouped by day, limited by count and/or leadtime."""
        entries = []

        iterator = itertools.groupby(
            self._filter(
                self._entries,
                leadtime=leadtime,
                types=types,
                include_today=include_today,
            ),
            lambda e: e.date,
        )

        for key, group in iterator:
            entries.append(CollectionAppointmentGroup.create(list(group)))
        if count is not None:
            entries = entries[:count]

        return entries

    def _filter(
        self, entries, count=None, leadtime=None, types=None, include_today=False
    ):
        # remove unwanted waste types
        if types is not None:
            # generate set
            types_set = set(t for t in types)
            entries = list(filter(lambda e: e.type in types_set, self._entries))

        # remove expired entries
        now = datetime.datetime.now().date()
        if include_today:
            entries = list(filter(lambda e: e.date >= now, entries))
        else:
            entries = list(filter(lambda e: e.date > now, entries))

        # remove entries which are too far in the future (0 = today)
        if leadtime is not None:
            x = now + datetime.timedelta(days=leadtime)
            entries = list(filter(lambda e: e.date <= x, entries))

        # ensure that entries are sorted by date
        entries.sort(key=lambda e: e.date)

        # remove surplus entries
        if count is not None:
            entries = entries[:count]

        return entries

    @staticmethod
    def create(source_name: str, dir_offset, customize: {}, kwargs):
        # load source module

        # for home-assistant, use the last 3 folders, e.g. custom_component/wave_collection_schedule/package
        # otherwise, only use package
        folders = os.path.normpath(os.path.dirname(__file__)).split(os.sep)[dir_offset:]
        path = ".".join(folders) + ".source." + source_name
        try:
            source_module = importlib.import_module(path)
        except ImportError:
            _LOGGER.error(f"source module not found: {path}")
            return

        # create source
        source = source_module.Source(**kwargs)

        # create scraper
        g = Scraper(source, customize)

        return g


if __name__ == "__main__":
    scraper = Scraper.create("abfall_kreis_tuebingen", {}, {"ort": 3, "dropzone": 525})
    scraper.fetch()
    entries = scraper.get_upcoming()
    for e in entries:
        print(f"{e}, daysTo={e.daysTo}")
    print("========")
    types = scraper.get_types()
    for t in types:
        print(t)
    print("========")
    entries = scraper.get_upcoming_group_by_day()
    for e in entries:
        print(e)
    print("========")
