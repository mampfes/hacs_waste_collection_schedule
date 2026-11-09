# Waste Collection dashboard cards

The integration bundles three cards. They work with the integration's calendars
for any country, source or waste type, including the generic ICS source. A card
can show one or several properties without merging their collections. They also
work with other Home Assistant calendars when selected explicitly.

- **Waste Collection · Next pickup**: every waste type collected on the next day
  with a collection. With several calendars, each calendar shows its own next
  day under its name.
- **Waste Collection · Schedule**: an agenda grouped by collection date.
- **Waste Collection · Bins**: the next collection for each waste type per calendar.
  It looks 90 days ahead by default (the others 30), so less frequent bins still show.

## Add a card

Automatic card registration requires **Home Assistant 2025.5 or newer**. Use
**Home Assistant 2026.6 or newer** for the visual editor's repeatable waste-type
style fields; on 2025.5–2026.5 configure the cards in YAML. Older supported HA
versions skip card registration and retain their existing schedules. The integration
minimum remains 2024.4.0. The cards need the `frontend`, `http` and `lovelace` components.

After updating the integration, restart Home Assistant and reload your browser.
Open a dashboard, choose **Edit dashboard → Add card**, and search for **Waste
Collection**. Select your waste calendar(s) in the visual editor. The picker
suggests calendars owned by this integration, excluding disabled/hidden entities.
If you have only sensors, enable the source's calendar or select its main
calendar; the cards read the calendar API rather than parsing sensor display text.

The integration registers the module resource automatically in storage mode.
For YAML dashboard resource management, the frontend also loads it automatically.
If managing resources yourself, use a module resource at
`/waste_collection_schedule/waste-collection-cards.js`. Do not load a second copy
from `/local/`. Headless installs do not need to load the frontend. Removing the
last entry of the integration (with no YAML configuration left) also removes the
managed resource (or the extra JavaScript URL in YAML mode). The storage-mode
resource is integration-managed: deleting it manually does not opt out, and it
will be re-created the next time Home Assistant starts.

## Customisation

Every card has a visual editor for title, calendars, days ahead (1–366), item limit
(1–100), dates, countdowns, icons, images, colours, inclusion/exclusion lists and waste-type
styles. Styles match the **exact calendar event summary**, before any display
rename. Each style can set a label, icon, colour and image. Styling a waste type
does not alter the source, calendar, sensors or other cards.

No country-specific colour assumptions are made. When `show_colors` is enabled
(default), a style's colour — or, if unset, the calendar's published waste-type
colour — tints the icon tile and draws its ring; names and dates use theme text
colours and remain readable for light/dark themes and colour-blind users. With
`show_colors: false` tiles stay neutral regardless of configured colours. Without
a card style, icons and images come from the source's `customize` settings, then
the calendar icon, then a neutral bin.
Images are optional: use `/local/...` paths or HTTPS URLs. Failed images fall back
to the icon. Prefer your own/local images to avoid third-party requests.

```yaml
type: custom:waste-collection-bins-card
title: Our collection
entities:
  - calendar.waste_collection
days: 60
max_items: 12
show_countdown: true
show_date: true
show_icons: true
show_pictures: true
show_colors: true
types:
  - type: Paper
    name: Paper and cardboard
    icon: mdi:package-variant
    color: '#2196f3'
    picture: /local/paper-bin.png
  - type: Glass
    icon: mdi:glass-fragile
    color: '#4caf50'
```

Replace `type` with `custom:waste-collection-next-card` or
`custom:waste-collection-schedule-card` to use another layout. Use `include_types`
or `exclude_types` lists to filter exact summaries. `max_items` caps visible events
(or bins); choose a high enough value to show every same-day collection.

## Dates, accessibility and updates

All-day dates are preserved as calendar days. Timed events and today's date use
Home Assistant's time zone (or the browser zone if your HA profile selects local
time). Calendar-day arithmetic avoids DST countdown errors. Dates and countdowns
use the selected HA language; `language` can override it per card. UI labels are
translated into English, German, French and Italian, with English fallback for
other languages. Waste names remain as provided unless you customise them.

Cards support Sections resizing (`getGridOptions`) and masonry sizing. Native
buttons support touch and keyboard; selecting a pickup opens calendar more-info.
Long labels wrap, theme tokens follow HA font scaling, and colour never carries meaning alone.
On HA 2026.11 and newer, calendar names follow HA’s device/entity naming policy.
Narrow Sections cards stack their content so names remain readable. Background
refreshes keep existing pickups and keyboard focus visible.
The schedule content scrolls within a resized card.

Cards reload when selected calendar states change, every five minutes and after
local midnight. Removed cards cancel timers/subscriptions and ignore pending
responses. A short shared request cache avoids duplicate calls across cards.
Loading, empty periods, failed calendars and partial failures are distinct states.
Retry refreshes the calendar API; use the integration's Fetch data action to
refresh a provider itself. A successful but stale upstream calendar cannot be
detected by the frontend alone.

## Development and verification

```sh
cd frontend
npm ci
npm run typecheck  # TypeScript 7.0.2 native compiler
npm test
npm run test:browser
npm run build
```

Commit the bundle under the integration's `frontend/` directory. CI rebuilds and
checks it against the TypeScript sources. Browser tests cover regional names,
simultaneous pickups, time zones/DST, rollover, keyboard actions, long labels,
errors and light/dark accessibility. These tests use fixture calendar responses;
real provider and live HA rendering checks are separate deployment steps.

No community card code or remote images are bundled.
The build generates `THIRD-PARTY-NOTICES.txt` beside the JavaScript bundle with
the complete licenses for its Lit dependencies. Ship both files together.

These cards target the `release/3.0.0` integration and use its calendar API and
collection attributes. They preserve the release branch’s entry migration,
schedule cache and repair cleanup.
