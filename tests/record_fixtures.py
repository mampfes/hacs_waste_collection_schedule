"""Record a source's live HTTP as offline cassettes.

Run manually (never in CI) to capture or refresh cassettes::

    python tests/record_fixtures.py stirling_wa_gov_au [other_module ...]
    python tests/record_fixtures.py --all          # every new-arch source

For each TEST_CASE it runs the full ``fetch()`` once against the live provider,
recording every HTTP interaction (across the curl_cffi and requests stacks) to
``tests/fixtures/<module>/<case_slug>.json`` together with the recording date.
Review the diff and commit; CI then replays those cassettes offline.
"""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import datetime
import glob
import os
import re
import sys

import dateutil.parser  # noqa: F401

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

from importlib import import_module  # noqa: E402

import cassette  # noqa: E402
from fixtures_support import fixture_path, slug  # noqa: E402

SOURCE_DIR = os.path.join(
    os.path.dirname(__file__),
    "../custom_components/waste_collection_schedule/waste_collection_schedule/source",
)


def _new_arch_modules() -> list[str]:
    mods = []
    for path in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.py"))):
        if re.search(
            r"class Source\(BaseSource\)", open(path, encoding="utf-8").read()
        ):
            mods.append(os.path.basename(path)[:-3])
    return mods


def record(module_name: str) -> None:
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    today = datetime.date.today().isoformat()
    for case_key, args in module.Source.TEST_CASES.items():
        path = fixture_path(module_name, case_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with cassette.recording(path, today):
                results = module.Source(**args).fetch()
            if not results:
                # An empty fetch makes a useless cassette (provider down or a
                # stale test case); drop it rather than record nothing.
                if os.path.exists(path):
                    os.remove(path)
                print(f"  ! {case_key}: fetch returned no collections, skipped")
                continue
            print(f"  recorded {slug(case_key)} ({len(results)} collections)")
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"  ! {case_key}: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    args = sys.argv[1:]
    modules = _new_arch_modules() if args == ["--all"] else args
    if not modules:
        print(__doc__)
        sys.exit(1)
    for mod in modules:
        print(f"== {mod} ==")
        record(mod)
