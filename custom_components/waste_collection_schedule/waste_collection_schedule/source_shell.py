import datetime
import fnmatch
import importlib
import logging
import traceback
from collections.abc import Iterable
from typing import Protocol, cast

from .collection import Collection, LegacyCollection
from .colors import validate_color

_LOGGER = logging.getLogger(__name__)

# Characters that mark a customize key as an fnmatch glob pattern.
_GLOB_CHARS = "*?["


def _is_glob(key: str) -> bool:
    return any(ch in key for ch in _GLOB_CHARS)


def _match_customize_keys(
    customize: dict[str, "Customize"], keys: list[str]
) -> "Customize | None":
    """Return the Customize entry matching any of ``keys``.

    An exact key match always wins and is tried for every candidate key (in the
    order given) before any glob is considered, so an exact match on one key can
    never be shadowed by a glob match on another. If no candidate matches
    exactly, each candidate is matched against every customize key that contains
    an fnmatch glob wildcard (``*``, ``?`` or ``[...]``); the first such glob key
    in definition order wins. Matching is case-sensitive, like the exact lookup.
    """
    for key in keys:
        c = customize.get(key)
        if c is not None:
            return c
    for pattern, candidate in customize.items():
        if _is_glob(pattern) and any(fnmatch.fnmatchcase(k, pattern) for k in keys):
            return candidate
    return None


def match_customize(
    customize: dict[str, "Customize"], waste_type: str
) -> "Customize | None":
    """Return the Customize entry for a single waste-type key.

    An exact key match always wins. If no exact key exists, the waste type is
    matched against any customize key that contains an fnmatch glob wildcard
    (``*``, ``?`` or ``[...]``), e.g. ``"Sonderabfall *"``. The first matching
    glob key (in definition order) is used. Matching is case-sensitive, like
    the exact lookup.
    """
    return _match_customize_keys(customize, [waste_type])


class Fetchable(Protocol):
    def fetch(self) -> list[Collection]: ...


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
        color: str | None = None,
    ):
        self._waste_type = waste_type
        self._alias = alias
        self._show = show
        self._icon = icon
        self._picture = picture
        self._color = validate_color(color) if color is not None else None
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
    def color(self) -> str | None:
        return self._color

    @property
    def use_dedicated_calendar(self):
        return self._use_dedicated_calendar

    @property
    def dedicated_calendar_title(self):
        return self._dedicated_calendar_title

    def __repr__(self):
        return f"Customize{{waste_type={self._waste_type}, alias={self._alias}, show={self._show}, icon={self._icon}, picture={self._picture}}}"


def _get_customize_key(entry: Collection) -> str:
    """Primary key used to look an entry up in the customize dict.

    New-style sources: the canonical ``WasteType.id`` (e.g. "general_waste"),
    which is stable and locale-independent.
    Legacy sources: the display string (e.g. "Refuse").
    """
    if isinstance(entry, LegacyCollection):
        return entry.type
    return entry.waste_type.id


def _customize_keys(entry: Collection) -> list[str]:
    """Candidate keys to look an entry up in the customize dict.

    Legacy sources are only ever matched by their display string, exactly as
    before. New-style (pipeline) sources are matched by their canonical
    ``WasteType.id`` first, then by the localised display name, then by the
    entry's ``description`` (if any) as a last-resort fallback.

    The display-name fallback is what actually fixes per-type customisation for
    pipeline sources (issue #6936): the config flow presents, stores and builds
    sensors from the display labels the user sees, so every customize key the UI
    writes is a display name, never an id. Accepting both keys lets that stored
    customisation apply while keeping the id as the preferred, locale-independent
    key (and the one the library's own tests assert). User-typed fnmatch globs,
    also written against the displayed labels, keep working for the same reason.

    The ``description`` fallback exists because a ``type_value_map`` can map
    several distinct provider labels onto one canonical WasteType (e.g.
    Neunkirchen Siegerland's "Restmülltonne"/"Spartonne Restmüll"/"Container
    Restmüll" all resolve to General Waste) — the source carries the original
    label into ``description`` in that case, and matching customize keys
    against it too is what lets a user hide (or rename/re-icon) just the one
    variant that doesn't apply to their address, by writing a customize entry
    keyed on that raw label (exactly or via glob), without losing the other
    variant(s) they do have.
    """
    if isinstance(entry, LegacyCollection):
        return [entry.type]
    # id and display name preferred; de-duplicate in case either equals the
    # description (e.g. an English preserved label, or no description set).
    keys = [entry.waste_type.id, entry.type]
    if entry.description:
        keys.append(entry.description)
    return list(dict.fromkeys(keys))


def filter_function(entry: Collection, customize: dict[str, Customize]):
    c = _match_customize_keys(customize, _customize_keys(entry))
    if c is None:
        return True
    return c.show


def customize_function(entry: Collection, customize: dict[str, Customize]):
    c = _match_customize_keys(customize, _customize_keys(entry))
    if c is not None:
        if c.alias is not None:
            entry.set_type(c.alias)
        if c.icon is not None:
            entry.set_icon(c.icon)
        if c.picture is not None:
            entry.set_picture(c.picture)
        if c.color is not None:
            entry.set_color(c.color)
    return entry


def apply_day_offset(entry: Collection, day_offset: int) -> Collection:
    entry.set_date(entry.date + datetime.timedelta(days=day_offset))
    return entry


class SourceShell:
    def __init__(
        self,
        source: Fetchable,
        customize: dict[str, Customize],
        title: str,
        description: str,
        url: str | None,
        calendar_title: str | None,
        unique_id: str,
        day_offset: int,
        ignore_duplicates: bool = False,
    ):
        self._source = source
        self._customize = customize
        self._title = title
        self._description = description
        self._url = url
        self._calendar_title = calendar_title
        self._unique_id = unique_id
        self._refreshtime: datetime.datetime | None = None
        self._entries: list[Collection] = []
        self._day_offset = day_offset
        self._ignore_duplicates = ignore_duplicates

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

    def fetch(self) -> bool:
        """Fetch data from source and report whether it succeeded."""
        try:
            # fetch returns a list of Collection's
            entries: Iterable[Collection] = self._source.fetch()
        except Exception:
            _LOGGER.error(
                f"fetch failed for source {self._title}:\n{traceback.format_exc()}"
            )
            return False
        self._refreshtime = datetime.datetime.now()

        # Strip incidental whitespace from legacy sources' raw type strings.
        #
        # Restricted to LegacyCollection (and only when stripping actually
        # changes something): calling set_type() unconditionally on every
        # entry would set Collection._type_override on pipeline-sourced
        # entries too, which makes Collection._identity_key (and therefore
        # equality/hashing/dedup) fall back to the localised display string
        # instead of the locale-independent WasteType.id, defeating its
        # purpose (#6942). Pipeline entries' display names come from the
        # controlled WASTE_TYPES catalogue and are not expected to carry
        # incidental whitespace, so they are left untouched here.
        for e in entries:
            if isinstance(e, LegacyCollection):
                stripped = e.type.strip()
                if stripped != e.type:
                    e.set_type(stripped)

        # filter hidden entries
        entries = filter(lambda x: filter_function(x, self._customize), entries)

        # customize fetched entries
        entries = (customize_function(x, self._customize) for x in entries)

        # apply day offset
        if self._day_offset != 0:
            entries = (apply_day_offset(x, self._day_offset) for x in entries)

        result = list(entries)

        # Remove duplicate (date, identity) pairs, folding any distinguishing
        # description from a discarded duplicate into the entry that's kept
        # instead of just dropping it.
        #
        # Keyed on Collection._identity_key (locale-independent: the
        # customize alias if one was set, else the canonical WasteType.id),
        # not the displayed .type — two entries must not compare equal in one
        # UI language and unequal in another. This also catches a case that
        # slipping .type in as the key could not: a source's type_value_map
        # can map several distinct provider labels (e.g. a bin-size or
        # rhythm variant it can't yet filter by) onto one canonical type, and
        # where the underlying schedules overlap on some dates, the two
        # entries for that day would otherwise show up as a visible
        # duplicate once canonicalisation makes their labels identical (see
        # abfall_neunkirchen_siegerland_de and koppl_at).
        if self._ignore_duplicates:
            by_key: dict[tuple, Collection] = {}
            order: list[tuple] = []
            for e in result:
                key = (e.date, e._identity_key)
                kept = by_key.get(key)
                if kept is None:
                    by_key[key] = e
                    order.append(key)
                elif e.description and e.description != kept.description:
                    merged = ", ".join(
                        dict.fromkeys(filter(None, [kept.description, e.description]))
                    )
                    kept.set_description(merged)
            result = [by_key[key] for key in order]

        self._entries = result
        return True

    def get_dedicated_calendar_types(self) -> set[str]:
        """Return set of waste types with a dedicated calendar.

        Dedicated calendars require an exact type key. Glob customize keys are
        skipped here: a single pattern can match many fetched types, so a
        per-type dedicated calendar cannot be derived from it.
        """
        types = set()

        for key, customize in self._customize.items():
            if _is_glob(key):
                continue
            if customize.show and customize.use_dedicated_calendar:
                types.add(key)

        return types

    def get_calendar_title_for_type(self, type: str) -> str:
        """Return calendar title for waste type (used for dedicated calendars)."""
        c = match_customize(self._customize, type)
        if c is not None and c.dedicated_calendar_title:
            return c.dedicated_calendar_title

        return self.get_collection_type_name(type)

    def get_collection_type_name(self, type: str) -> str:
        c = match_customize(self._customize, type)
        if c is not None and c.alias:
            return c.alias

        return type

    @staticmethod
    def create(
        source_name: str,
        customize: dict[str, Customize],
        source_args,
        calendar_title: str | None = None,
        day_offset: int = 0,
        ignore_duplicates: bool | None = None,
    ) -> "SourceShell | None":
        """Build a SourceShell for ``source_name``.

        ``ignore_duplicates=None`` means "the user hasn't explicitly set this
        option on this config entry yet" — resolved below to the source's own
        declared default (``IGNORE_DUPLICATES_DEFAULT``), falling back to
        ``False`` if it declares none. Pass an explicit ``True``/``False`` to
        apply the user's stored choice instead, which always wins over the
        source's default (a user who explicitly wants duplicates merged, or
        explicitly doesn't, is not overridden by the source's opinion).
        """
        # load source module
        try:
            source_module: SourceModule = cast(
                SourceModule,
                importlib.import_module(
                    f"waste_collection_schedule.source.{source_name}"
                ),
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
        try:
            source: Fetchable = source_module.Source(**source_args)  # type: ignore
        except Exception as e:
            _LOGGER.error(
                f"error creating source {source_name} with arguments "
                f"{source_args}: {e}\n"
                "This is usually caused by a stale/invalid configuration, e.g. "
                "after the source's arguments changed in an update, or a "
                "'customize' entry that was nested under 'args' instead of "
                "being a sibling of it. Please check the source's "
                f"documentation and reconfigure it.\n{traceback.format_exc()}"
            )
            return None

        # read metadata from Source class first, fall back to module level
        source_cls = source_module.Source
        title: str = (
            getattr(source_cls, "TITLE", None)
            or getattr(source_module, "TITLE", "")
            or ""
        )
        description: str = (
            getattr(source_cls, "DESCRIPTION", None)
            or getattr(source_module, "DESCRIPTION", "")
            or ""
        )
        url: str = (
            getattr(source_cls, "URL", None) or getattr(source_module, "URL", "") or ""
        )
        if ignore_duplicates is None:
            ignore_duplicates = _resolve_ignore_duplicates_default(
                source_cls, source_module
            )

        # create source shell
        g = SourceShell(
            source=source,
            customize=customize,
            title=title,
            description=description,
            url=url,
            calendar_title=calendar_title,
            unique_id=calc_unique_source_id(source_name, source_args),
            day_offset=day_offset,
            ignore_duplicates=ignore_duplicates,
        )

        return g


def calc_unique_source_id(source_name: str, source_args) -> str:
    return source_name + str(sorted(source_args.items()))


def _resolve_ignore_duplicates_default(source_cls, source_module) -> bool:
    """A source's declared default for the "Ignore Duplicate Entries per Day"
    option: ``IGNORE_DUPLICATES_DEFAULT`` on the Source class (pipeline) first,
    else the same name at module level (legacy), else ``False``. Same
    class-then-module precedence already used for TITLE/DESCRIPTION/URL.
    """
    cls_value = getattr(source_cls, "IGNORE_DUPLICATES_DEFAULT", None)
    if cls_value is not None:
        return bool(cls_value)
    return bool(getattr(source_module, "IGNORE_DUPLICATES_DEFAULT", False))


def default_ignore_duplicates(source_name: str) -> bool:
    """The same resolution as ``SourceShell.create``, from just a source name.

    For the config flow to pre-fill the "Ignore Duplicate Entries per Day"
    option with the source's own opinion before the user has ever set it
    explicitly on this config entry. Returns ``False`` (never raises) if the
    source can't be imported — the config flow shouldn't fail over a
    pre-filled checkbox value.
    """
    try:
        source_module: SourceModule = cast(
            SourceModule,
            importlib.import_module(f"waste_collection_schedule.source.{source_name}"),
        )
        source_cls = source_module.Source
    except Exception:
        return False
    return _resolve_ignore_duplicates_default(source_cls, source_module)
