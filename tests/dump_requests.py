"""Dump every request a cassette replay issues, for before/after refactor diffs.

Replay does not prove a refactor left the outgoing requests alone. The cassette
key hashes only the first of ``json``/``data``/``params``, and when the key
misses, ``cassette.py`` falls back to matching on method and URL alone. So a
refactor that changes a request body or its query string still replays green,
having checked nothing about what was sent (#7102).

Until the harness pins them, this is how a migration that touches request
building is checked: dump the requests before and after and diff them.

    python tests/dump_requests.py awigo_de > before.txt
    ... refactor ...
    python tests/dump_requests.py awigo_de > after.txt
    diff before.txt after.txt

With no module names it dumps every cassette in the tree.
"""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import contextlib
import os
import sys

import dateutil.parser  # noqa: F401

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

from importlib import import_module

import cassette
from curl_cffi import requests as _cffi
from fixtures_support import discover_fixtures, slug
from requests import sessions as _requests_sessions


def _resolve_case(module_name: str, case_slug: str):
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    for key, args in module.Source.TEST_CASES.items():
        if slug(key) == case_slug:
            return module.Source, args
    return None, None


def _describe(method: str, url: str, kwargs: dict) -> str:
    """One line per request: what was sent, in a stable order."""
    parts = [f"{method.upper()} {url}"]
    for name in ("params", "data", "json"):
        value = kwargs.get(name)
        if value is None:
            continue
        if isinstance(value, dict):
            rendered = ", ".join(f"{k}={value[k]!r}" for k in value)
        else:
            rendered = repr(value)
        parts.append(f"  {name}: {rendered}")
    return "\n".join(parts)


@contextlib.contextmanager
def _recording(sink: list):
    """Wrap whatever cassette already patched, logging each call through it."""
    cffi_request = _cffi.Session.request
    plain_request = _requests_sessions.Session.request
    plain_send = _requests_sessions.Session.send

    def wrap(original):
        def wrapper(self, method, url, *args, **kwargs):
            sink.append(_describe(method, url, kwargs))
            return original(self, method, url, *args, **kwargs)

        return wrapper

    def wrap_send(original):
        def wrapper(self, request, *args, **kwargs):
            # The prepared-request path: params are already folded into the URL.
            sink.append(_describe(request.method, request.url, {}))
            return original(self, request, *args, **kwargs)

        return wrapper

    _cffi.Session.request = wrap(cffi_request)
    _requests_sessions.Session.request = wrap(plain_request)
    _requests_sessions.Session.send = wrap_send(plain_send)
    try:
        yield
    finally:
        _cffi.Session.request = cffi_request
        _requests_sessions.Session.request = plain_request
        _requests_sessions.Session.send = plain_send


def main(wanted: "list[str]") -> int:
    for module_name, case_slug, path in sorted(discover_fixtures()):
        if wanted and module_name not in wanted:
            continue
        cls, args = _resolve_case(module_name, case_slug)
        if cls is None:
            print(f"{module_name}::{case_slug}: NO MATCHING TEST_CASE")
            continue
        sent: list[str] = []
        try:
            with (
                open(os.devnull, "w") as quiet,
                contextlib.redirect_stdout(quiet),
                contextlib.redirect_stderr(quiet),
                cassette.replaying(path),
                _recording(sent),
            ):
                cls(**args).fetch()
        except Exception as error:
            sent.append(f"RAISED {type(error).__name__}: {error}")
        print(f"{module_name}::{case_slug}: {len(sent)} requests")
        for line in sent:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
