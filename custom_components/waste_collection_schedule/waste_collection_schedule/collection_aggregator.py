import itertools
import logging
from collections.abc import Iterable, Sequence
from datetime import date, datetime, timedelta

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
        unique_types: bool = False,
        preserve_bins: bool = False,
    ) -> list[Collection]:
        """Return list of all entries, limited by count and/or leadtime.

        Keyword arguments:
        count -- limits the number of returned entries (default=10)
        leadtime -- limits the timespan in days of returned entries (default=7, 0 = today)
        """
        include_types = tuple(include_types) if include_types is not None else None
        exclude_types = tuple(exclude_types) if exclude_types is not None else None
        return self._filter(
            self._filter_entries(
                include_types, exclude_types, unique_types, preserve_bins
            ),
            count=count,
            leadtime=leadtime,
            include_types=include_types,
            exclude_types=exclude_types,
            include_today=include_today,
            start_index=start_index,
            unique_types=unique_types,
        )

    def get_upcoming_group_by_day(
        self,
        count: int | None = None,
        leadtime: int | None = None,
        include_types: Iterable[str] | None = None,
        exclude_types: Iterable[str] | None = None,
        include_today: bool = False,
        start_index: int | None = None,
        unique_types: bool = False,
    ) -> list[CollectionGroup]:
        """Return list of all entries, grouped by day, limited by count and/or leadtime."""
        include_types = tuple(include_types) if include_types is not None else None
        exclude_types = tuple(exclude_types) if exclude_types is not None else None
        entries = []

        iterator = itertools.groupby(
            self._filter(
                self._filter_entries(include_types, exclude_types, unique_types),
                leadtime=leadtime,
                include_types=include_types,
                exclude_types=exclude_types,
                include_today=include_today,
                unique_types=unique_types,
            ),
            lambda e: e.date,
        )

        bins = self._filter(
            self._filter_entries(include_types, exclude_types, unique_types, True),
            leadtime=leadtime,
            include_types=include_types,
            exclude_types=exclude_types,
            include_today=include_today,
            unique_types=unique_types,
        )
        bin_records: dict[date, list[dict]] = {}
        for event in bins:
            bin_records.setdefault(event.date, []).append(event.as_dict())
        for day, group in iterator:
            grouped = CollectionGroup.create(list(group))
            # Display grouping can merge duplicate category names, while cards
            # still receive each provider bin's own identity and effective color.
            grouped._collections = bin_records.get(day, [])
            entries.append(grouped)
        if start_index is not None:
            entries = entries[start_index:]
        if count is not None:
            entries = entries[:count]

        return entries

    @staticmethod
    def matches_type(entry: Collection, value: str) -> bool:
        """Match canonical ids first, then the displayed or retained provider label."""
        return value in (entry.waste_type.id, entry.type, entry.original_label)

    def _filter_entries(
        self, include_types, exclude_types, unique_types, preserve_bins=False
    ):
        if (
            not include_types
            and not exclude_types
            and not unique_types
            and not preserve_bins
        ):
            return self._entries
        result = []
        for shell in self._shells:
            entries = getattr(shell, "_sensor_entries", None) or shell._entries
            seen = set()
            for entry in entries:
                if include_types and not any(
                    self.matches_type(entry, t) for t in include_types
                ):
                    continue
                if exclude_types and any(
                    self.matches_type(entry, t) for t in exclude_types
                ):
                    continue
                # Filter before merging. A retained label is also the identity
                # for next-of-each lists, including bins collected on one day.
                identity = (
                    (entry.waste_type.id, entry.original_label or entry._identity_key)
                    if preserve_bins
                    else entry.original_label
                    if unique_types
                    else entry._identity_key
                )
                key = (entry.date, identity or entry.waste_type.id)
                if getattr(shell, "_ignore_duplicates", False) and key in seen:
                    continue
                seen.add(key)
                result.append(entry)
        return result

    def _filter(
        self,
        entries,
        count: int | None = None,
        leadtime: int | None = None,
        include_types: Iterable[str] | None = None,
        exclude_types: Iterable[str] | None = None,
        include_today: bool = False,
        start_index: int | None = None,
        unique_types: bool = False,
    ) -> list[Collection]:
        # remove unwanted waste types from include list
        if include_types is not None:
            entries = list(
                filter(
                    lambda e: any(self.matches_type(e, t) for t in include_types),
                    entries,
                )
            )

        # remove unwanted waste types from exclude list
        if exclude_types is not None:
            entries = list(
                filter(
                    lambda e: not any(self.matches_type(e, t) for t in exclude_types),
                    entries,
                )
            )

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

        if unique_types:
            seen = set()
            unique = []
            for entry in entries:
                key = entry.original_label or entry.waste_type.id
                if key not in seen:
                    seen.add(key)
                    unique.append(entry)
            entries = unique

        # remove surplus entries
        if start_index is not None:
            entries = entries[start_index:]
        if count is not None:
            entries = entries[:count]

        return entries
