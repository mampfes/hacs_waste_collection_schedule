"""Validate a provider response against a declared, typed shape.

A source declares the shape of the raw data it expects (a ``TypedDict`` for an
object, ``list[...]`` for an array, nested as needed). That one declaration does
three jobs:

* **static typing** — pyright checks the parse/transform code against the shape;
* **offline fixtures** — recorded responses are validated on replay, so the
  fixtures stay faithful to the declared shape;
* **runtime diagnostics** — in production, a response that no longer matches the
  shape (the provider changed its API) raises :class:`ResponseShapeError` with
  the offending data logged, so a user can paste it straight into a bug report.

The validator is deliberately shallow-but-structural: it checks container kinds,
required ``TypedDict`` keys and primitive types, not every leaf value, so it
flags a genuinely changed shape without being brittle about, say, an extra key.
"""

from __future__ import annotations

import logging
import typing
from typing import Any, get_args, get_origin

_LOGGER = logging.getLogger(__name__)

# How much of an offending response to log, so a bug report is useful without
# dumping megabytes.
_SAMPLE_CHARS = 2000


class ResponseShapeError(Exception):
    """A provider response did not match the source's declared shape.

    Signals that the provider likely changed its API. The message points the
    user at the logged response so they can include it when reporting.
    """

    def __init__(self, source_name: str, detail: str):
        self.source_name = source_name
        self.detail = detail
        super().__init__(
            f"{source_name}: the provider's response did not match the expected "
            f"shape ({detail}). The provider may have changed its API; please "
            f"report this and include the response logged above."
        )


def validate(data: Any, shape: Any, *, source_name: str = "source") -> Any:
    """Return ``data`` if it matches ``shape``, else log it and raise.

    ``shape`` may be a ``TypedDict`` class, a ``list[...]`` / ``dict[...]``
    generic alias, ``X | None``, a primitive type, or ``Any`` (skips).
    """
    problem = _check(data, shape, "$")
    if problem is not None:
        _LOGGER.warning(
            "%s: response shape mismatch (%s). Raw response sample:\n%.*s",
            source_name,
            problem,
            _SAMPLE_CHARS,
            repr(data),
        )
        raise ResponseShapeError(source_name, problem)
    return data


def _check(data: Any, shape: Any, path: str) -> str | None:
    """Return a human-readable problem string, or None when ``data`` fits."""
    if shape is Any or shape is None or shape is object:
        return None

    origin = get_origin(shape)

    # Optional / unions: any member matching is a pass.
    if origin is typing.Union:
        members = get_args(shape)
        if any(_check(data, m, path) is None for m in members):
            return None
        names = ", ".join(getattr(m, "__name__", str(m)) for m in members)
        return f"{path}: {type(data).__name__} matched none of ({names})"

    if typing.is_typeddict(shape):
        if not isinstance(data, dict):
            return (
                f"{path}: expected object ({shape.__name__}), got {type(data).__name__}"
            )
        hints = typing.get_type_hints(shape)
        for key in getattr(shape, "__required_keys__", set()):
            if key not in data:
                return f"{path}.{key}: required key missing"
            problem = _check(data[key], hints.get(key, Any), f"{path}.{key}")
            if problem:
                return problem
        return None

    if origin in (list, tuple):
        if not isinstance(data, list):
            return f"{path}: expected list, got {type(data).__name__}"
        args = get_args(shape)
        if args:
            elem_shape = args[0]
            for i, item in enumerate(data):
                problem = _check(item, elem_shape, f"{path}[{i}]")
                if problem:
                    return problem
        return None

    if origin is dict:
        if not isinstance(data, dict):
            return f"{path}: expected dict, got {type(data).__name__}"
        return None

    if isinstance(shape, type):
        # Primitive: bool is not an int here; allow int where float is declared.
        if shape is float and isinstance(data, int) and not isinstance(data, bool):
            return None
        if not isinstance(data, shape):
            return f"{path}: expected {shape.__name__}, got {type(data).__name__}"
        return None

    return None
