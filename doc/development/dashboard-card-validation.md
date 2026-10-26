# Dashboard card validation

Validated on 26 October 2026 on branch `feat/waste-dashboard-cards`.

## Automated checks

- TypeScript 7.0.2 native compiler: passed.
- Frontend model tests: 10 passed, covering date-only/timed calendar events,
  international time zones, DST countdowns, input validation, regional labels,
  deduplication and safe image URLs.
- Playwright: 13 passed, including simultaneous pickups, keyboard more-info,
  long labels, mobile overflow, errors/partial failures, stale responses,
  midnight rollover, image fallback, and light/dark axe checks.
- Python 3.14 / Home Assistant 2026.10.4: 197 passed.
- Python 3.12 / Home Assistant 2024.4.0: 191 passed; six frontend tests skipped
  because this minimum HA version lacks the asynchronous static-path API.
- Changed-file pre-commit: Ruff, codespell, Bandit, YAML formatting, JSON and
  mypy passed.
- CodeRabbit CLI sanity review: completed with zero findings across 27 files.
- Production bundle rebuilt locally; deployed bytes checked with SHA-256.
- Home Assistant configuration check passed before restart.

## Live Home Assistant

The integration files were installed but no provider was configured. Configured
the existing generic ICS source for Moreton Bay using the council's published
Thursday/week-2 feed after the council property lookup. No provider code or
generated source documentation was changed. Personal address information is
intentionally absent from this repository.

Backed up the installed integration and blank Waste Collection dashboard before
deployment. Registered the bundled module resource and updated only the Waste
Collection dashboard through the HA API. The release version remains 2.36.0;
the module URL includes a build content hash.

Verified through HA-MCP and the actual Home Assistant browser:

- The integration calendar is available and supplies real occurrences.
- The next collection on 29 October includes general waste and recycling;
  garden organics appears on 5 November.
- All three cards display these data with per-card names, icons and accents.
- Dark-theme desktop and 390 x 844 phone layouts render without horizontal
  overflow. Phone sections stack and bin labels wrap.
- The native editor exposes calendar selectors and expandable Appearance,
  Waste type styles and Filters panels.
- Editing a type name with keyboard input updates the preview. Appearance
  toggles update it too; these preview changes were cancelled.
- Selecting a pickup opens the calendar's native more-info dialog.
- No Waste Collection errors were present in the HA system-log API after restart.

These checks establish calendar/API compatibility without assumptions about
country or bin categories. They do not claim that every upstream provider was
contacted, or that every user theme/image combination passes contrast checks.
