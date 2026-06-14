# isort: skip_file
# Import order here is load-bearing and must not be reordered: CollectionGroup
# has to be exported before collection_aggregator (which does
# `from . import CollectionGroup`) is imported, or that import hits a circular
# import on the partially-initialised package.
from .collection import CollectionFactory as Collection  # noqa: F401
from .collection import (
    Collection as CollectionBase,
)  # noqa: F401 (backwards compat alias)
from .collection import CollectionGroup  # noqa: F401
from .collection_aggregator import CollectionAggregator  # noqa: F401
from .icons import Icons  # noqa: F401
from .source_shell import Customize, SourceShell  # noqa: F401
