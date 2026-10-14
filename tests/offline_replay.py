"""Aggregate cassette replay checks across pytest-xdist workers."""

import os
from types import ModuleType

import pytest

_MODULE = pytest.StashKey[ModuleType]()
_SELECTION = pytest.StashKey[dict]()
_REPORTS = pytest.StashKey[list[dict]]()
_ERRORS = pytest.StashKey[list[str]]()
_SUMMARY = pytest.StashKey[str]()
_KEY = "offline_replay"


def assert_fallback_budget(paths, fallbacks, matches, budget):
    """Apply the same request-pinning ceiling to serial or merged results."""
    per_cassette = {p: fallbacks.get(p, 0) for p in paths}
    total = sum(per_cassette.values())
    served = sum(matches.get(p, 0) for p in paths)
    using = {p: n for p, n in per_cassette.items() if n}
    worst = sorted(((n, p) for p, n in using.items()), reverse=True)[:10]
    detail = "\n".join(f"    {n:>4}  {os.path.relpath(p)}" for n, p in worst)
    summary = (
        f"{total} of {served} replayed requests matched on the loose "
        f"method+url fallback, across {len(using)} of {len(paths)} cassettes."
    )
    assert total <= budget, (
        f"{summary}\nThat is above the ceiling of {budget}. A fallback "
        "match is a request the cassette does not pin: its body is not "
        "compared, so a refactor can change what is sent and still replay "
        "green. Do not raise the ceiling. Re-record the cassette "
        "(`python tests/record_fixtures.py <module>`) so it carries request "
        "bodies, or fix whatever stopped the exact key matching.\n"
        f"  worst offenders:\n{detail}"
    )
    return summary


def merge_replay_reports(reports):
    """Require complete worker results before applying the global ceiling."""
    first = reports[0]
    completed = set()
    fallbacks, matches = {}, {}
    for report in reports:
        for key in ("paths", "required", "budget", "full"):
            assert report[key] == first[key], f"workers disagree on replay {key}"
        overlap = completed.intersection(report["completed"])
        assert not overlap, f"cassettes replayed by multiple workers: {sorted(overlap)}"
        completed.update(report["completed"])
        fallbacks.update(report["fallbacks"])
        matches.update(report["matches"])
    if not first["full"]:
        return "Filtered replay run: the full-cassette fallback check does not apply."
    missing = set(first["required"]) - completed
    assert not missing, f"cassettes not replayed to completion: {sorted(missing)}"
    missing_counters = set(first["paths"]) - (fallbacks.keys() & matches.keys())
    assert not missing_counters, f"missing replay counters: {sorted(missing_counters)}"
    return assert_fallback_budget(first["paths"], fallbacks, matches, first["budget"])


def pytest_configure(config):
    config.stash[_REPORTS] = []
    config.stash[_ERRORS] = []


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    if not hasattr(config, "workerinput"):
        return
    offline = [i for i in items if i.path.name == "test_offline_fixtures.py"]
    if not offline:
        return
    module = offline[0].module
    gate = next(
        (
            i
            for i in offline
            if i.name == "test_the_replay_fallback_budget_is_not_exceeded"
        ),
        None,
    )
    if gate is None:
        return
    paths = [os.path.abspath(p) for _, _, p in module._FIXTURES]
    paths += [os.path.abspath(p) for _, p in module._CHOICE_FIXTURES]
    required = paths + [os.path.abspath(p) for _, _, p in module._ERROR_FIXTURES]
    selected = {
        os.path.abspath(i.callspec.params["path"])
        for i in offline
        if hasattr(i, "callspec") and "path" in i.callspec.params
    }
    config.stash[_MODULE] = module
    config.stash[_SELECTION] = {
        "paths": sorted(paths),
        "required": sorted(required),
        "budget": module.FALLBACK_BUDGET,
        "full": selected.issuperset(required),
    }
    # The controller runs this check once after receiving every worker's data.
    items.remove(gate)
    config.hook.pytest_deselected(items=[gate])


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    report = node.workeroutput.get(_KEY)
    if error or report is None:
        node.config.stash[_ERRORS].append(
            f"missing results from {node.gateway.id}: {error}"
        )
    elif report:
        node.config.stash[_REPORTS].append(report)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    config = session.config
    if hasattr(config, "workerinput"):
        module = config.stash.get(_MODULE, None)
        config.workeroutput[_KEY] = (
            dict(
                config.stash[_SELECTION],
                completed=sorted(module._COMPLETED),
                fallbacks=dict(module.cassette.REPLAY_FALLBACKS),
                matches=dict(module.cassette.REPLAY_MATCHES),
            )
            if module is not None
            else {}
        )
        return
    reports = config.stash[_REPORTS]
    errors = config.stash[_ERRORS]
    if not reports and not errors:
        return
    try:
        assert not errors, "\n".join(errors)
        config.stash[_SUMMARY] = merge_replay_reports(reports)
        if session.exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED:
            # A filtered invocation may select only the deferred budget check.
            session.exitstatus = pytest.ExitCode.OK
    except AssertionError as exc:
        config.stash[_SUMMARY] = str(exc)
        if session.exitstatus == pytest.ExitCode.OK:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
        errors.append(str(exc))


def pytest_terminal_summary(terminalreporter, config):
    summary = config.stash.get(_SUMMARY, None)
    if summary is not None:
        failed = bool(config.stash[_ERRORS])
        terminalreporter.section("cassette replay validation", red=failed)
        terminalreporter.write_line(summary, red=failed)
