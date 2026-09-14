# Home Assistant 2026.9+ replaces voluptuous with its own shim (`probatio`) as
# a side effect of importing `homeassistant`: `probatio.compat.install_as_voluptuous()`
# runs on import and rebinds `sys.modules["voluptuous"]`, but any module that
# already did `import voluptuous as vol` before that point keeps its own
# reference to the real voluptuous. Whether `config_flow.py` and
# `test_config_flow.py` end up sharing the same `vol` class then depends on
# which test/source module happens to trigger `homeassistant`'s import first —
# an import-order race across the whole session. pytest guarantees this file
# loads before any test module in its tree, so importing `homeassistant` here
# pins the shim installation ahead of any stale `voluptuous` import,
# regardless of collection order.
import homeassistant  # noqa: F401
