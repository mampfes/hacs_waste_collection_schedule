"""Preprocessors: normalise parsed output into an iterable of records.

A preprocessor sits between ``parse`` and the transformer/classify step. It
takes whatever the parser produced and yields the individual records that the
transformer expects. This replaces the inline dict/list normalisation that
used to live in BaseSource.fetch().

Each preprocessor is a typed callable class::

    preprocessor = preprocessors.JsonPreprocessor()

The default used by BaseSource (DefaultPreprocessor) reproduces the historical
fetch() behaviour: a single dict becomes ``[dict]``, a falsy/None value becomes
``[]``, and an existing iterable passes through unchanged.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Protocol


class Preprocessor[InT, OutT](Protocol):
    """Normalise parsed output (InT) into an iterable of records (OutT)."""

    def __call__(self, records: InT) -> Iterable[OutT]: ...


class IdentityPreprocessor[T](Preprocessor[Iterable[T], T]):
    """Return the input iterable unchanged."""

    def __call__(self, records: Iterable[T]) -> Iterable[T]:
        return records


class IdentityIterablePreprocessor[T](Preprocessor[T, T]):
    """Wrap a non-iterable single record in a one-item list; pass iterables through."""

    def __call__(self, records: T) -> Iterable[T]:
        if isinstance(records, Iterable):
            return records
        return [records]


class JsonPreprocessor(Preprocessor[Any, Mapping[str, Any]]):
    """Normalise JSON parser output that is either a dict or a list of dicts.

    A single mapping yields one record; a list yields each mapping it contains
    (non-mapping entries are skipped). Anything else yields nothing.
    """

    def __call__(self, records: Any) -> Iterable[Mapping[str, Any]]:
        if isinstance(records, Mapping):
            yield records
        elif isinstance(records, Iterable):
            for entry in records:
                if isinstance(entry, Mapping):
                    yield entry


class KeyValuePreprocessor(Preprocessor[Any, Iterable[Mapping[str, str]]]):
    """Normalise key/value array records.

    Input of the form ``[[{name: ..., value: ...}], [{...}]]`` yields each
    inner iterable, filtered down to its mapping items.
    """

    def __call__(self, records: Any) -> Iterable[Iterable[Mapping[str, str]]]:
        if not isinstance(records, Iterable):
            return
        for entry in records:
            if not isinstance(entry, Iterable):
                continue
            yield [item for item in entry if isinstance(item, Mapping)]


class DefaultPreprocessor(Preprocessor[Any, Any]):
    """Reproduce the historical BaseSource.fetch() normalisation.

    - A falsy value (None, empty list, etc.) yields nothing.
    - A single mapping yields one record.
    - Any other iterable passes through unchanged.
    """

    def __call__(self, records: Any) -> Iterable[Any]:
        if not records:
            return
        if isinstance(records, Mapping):
            yield records
            return
        yield from records
