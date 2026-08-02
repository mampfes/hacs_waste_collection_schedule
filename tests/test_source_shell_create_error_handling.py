import os
import sys

# Make the core library importable as `waste_collection_schedule`.
sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.source_shell import SourceShell


def test_create_returns_none_and_logs_on_unexpected_kwarg(caplog):
    """A stale/invalid config (e.g. renamed/removed source argument, or a
    'customize' block accidentally nested under 'args') must not raise and
    crash the whole integration setup. It should be logged and skipped so
    other, correctly configured sources keep working."""
    shell = SourceShell.create(
        source_name="ics",
        customize={},
        source_args={"this_is_not_a_real_argument": "value"},
    )

    assert shell is None
    assert any(
        "error creating source ics" in record.message for record in caplog.records
    )


def test_create_succeeds_with_valid_args():
    """Sanity check: valid arguments still create a working shell."""
    test_file = os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule/waste_collection_schedule/test/test.ics",
    )
    shell = SourceShell.create(
        source_name="ics",
        customize={},
        source_args={"file": test_file},
    )

    assert shell is not None
