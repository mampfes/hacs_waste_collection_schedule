# HA 2026.9+ replaces `voluptuous` with its own `probatio` shim the first time
# `homeassistant` is imported: `probatio.compat.install_as_voluptuous()` re-points
# sys.modules["voluptuous"] at the shim, but any module that already did
# `import voluptuous as vol` keeps its reference to the real library. So
# `vol.Optional` in a test module and in config_flow.py can end up as two
# unrelated classes, depending on which import happened first — an import-order
# race across the whole session. pytest loads this conftest before any test
# module in its tree, so importing homeassistant here pins the swap ahead of
# every other import and closes the race regardless of collection order (#7415).
import homeassistant  # noqa: F401
