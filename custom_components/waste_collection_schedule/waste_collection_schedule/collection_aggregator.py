import itertools
import logging
from datetime import datetime, timedelta
from typing import Iterable, Sequence

from . import CollectionGroup
from .collection import Collection
from .source_shell import SourceShell

_LOGGER = logging.getLogger(__name__)


class CollectionAggregator:
    def __init__(self, shells: Sequence[SourceShell]):
        self._shells = shells

    @property
    def _entries(self) -> list[Collection]:
        """Merge all entries from all connected sources."""
        return [e for s in self._shells for e in s._entries]

    @property
    def refreshtime(self):
        """Simply return the timestamp of the first source."""
        return self._shells[0].refreshtime

    @property
    def types(self):
        """Return set() of all collection types."""
        return {e.type for e in self._entries}

    def get_upcoming(
        self,
        count: int | None = None,
        leadtime: int | None = None,
        include_types: Iterable[str] | None = None,
        exclude_types: Iterable[str] | None = None,
        include_today: bool = False,
        start_index: int | None = None,
    ) -> list[Collection]:
        """Return list of all entries, limited by count and/or leadtime.

        Keyword arguments:
        count -- limits the number of returned entries (default=10)
        leadtime -- limits the timespan in days of returned entries (default=7, 0 = today)
        """
        return self._filter(
            self._entries,
            count=count,
            leadtime=leadtime,
            include_types=include_types,
            exclude_types=exclude_types,
            include_today=include_today,
            start_index=start_index,
        )

    def get_upcoming_group_by_day(
        self,
        count: int | None = None,
        leadtime: int | None = None,
        include_types: Iterable[str] | None = None,
        exclude_types: Iterable[str] | None = None,
        include_today: bool = False,
        start_index: int | None = None,
    ) -> list[CollectionGroup]:
        """Return list of all entries, grouped by day, limited by count and/or leadtime."""
        entries = []

        iterator = itertools.groupby(
            self._filter(
                self._entries,
                leadtime=leadtime,
                include_types=include_types,
                exclude_types=exclude_types,
                include_today=include_today,
            ),
            lambda e: e.date,
        )

        for key, group in iterator:
            entries.append(CollectionGroup.create(list(group)))
        if start_index is not None:
            entries = entries[start_index:]
        if count is not None:
            entries = entries[:count]

        return entries

    def _filter(
        self,
        entries,
        count: int | None = None,
        leadtime: int | None = None,
        include_types: Iterable[str] | None = None,
        exclude_types: Iterable[str] | None = None,
        include_today: bool = False,
        start_index: int | None = None,
    ) -> list[Collection]:
        # remove unwanted waste types from include list
        if include_types is not None:
            entries = list(filter(lambda e: e.type in set(include_types), entries))

        # remove unwanted waste types from exclude list
        if exclude_types is not None:
            entries = list(filter(lambda e: e.type not in set(exclude_types), entries))

        # remove expired entries
        now = datetime.now().date()
        if include_today:
            entries = list(filter(lambda e: e.date >= now, entries))
        else:
            entries = list(filter(lambda e: e.date > now, entries))

        # remove entries which are too far in the future (0 = today)
        if leadtime is not None:
            x = now + timedelta(days=leadtime)
            entries = list(filter(lambda e: e.date <= x, entries))

        # ensure that entries are sorted by date
        entries.sort(key=lambda e: e.date)

        # remove surplus entries
        if start_index is not None:
            entries = entries[start_index:]
        if count is not None:
            entries = entries[:count]

        return entries
