# Waste collection dashboard card research

Research date: 26 October 2026. Exa and Tavily searches were checked against
official Home Assistant documentation, frontend source, and original community
repositories. Recommendations below are design decisions, not claims that the
implementation or live deployment has already passed validation.

## Home Assistant guidance

- **Sections first:** implement `getGridOptions()` with useful defaults and
  minimums. Sections have 12 columns, 56 px rows and 8 px gaps; default widths
  should be multiples of three. Keep `getCardSize()` for masonry dashboards.
  Content must still fit when resized or viewed on a phone.
  [Custom card API](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/),
  [dashboard design](https://contributors.home-assistant.io/design/dashboards/).
- **Simple, predictable interactions:** emphasize the next useful information,
  avoid clutter, and give interactive elements a clear affordance. Opening the
  entity's more-info dialog is the expected default action for an entity.
  Missing configuration and unavailable data need distinct, visible states.
  [Dashboard design](https://contributors.home-assistant.io/design/dashboards/),
  [official dashboard UX research](https://www.home-assistant.io/blog/2024/07/26/dashboard-chapter-2/).
- **Visual setup:** register each card in `window.customCards`, provide useful
  `getStubConfig()` defaults, and use `getConfigForm()` for simple native forms
  or `getConfigElement()` for a richer editor. A custom editor emits the complete
  config through a bubbling, composed `config-changed` event. Advanced options
  belong in expandable groups. Only suggest cards for compatible entities;
  entity suggestions are documented as available since HA 2026.6.
  [Card editor and picker](https://contributors.home-assistant.io/frontend/custom-ui/card-editor/).
- **Updates:** the developer guide now recommends requesting state data with
  `context-request` and cleaning up subscriptions on disconnect. The existing
  `hass` card API also remains documented; avoid rerendering for unrelated entity
  updates. Test behavior against the deployed HA version before depending on a
  newer API.
  [Developer guide](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/),
  [current card API](https://contributors.home-assistant.io/frontend/custom-ui/card/).
- **Themes:** use Home Assistant semantic CSS tokens, typography and spacing.
  Preserve support for commonly themed variables such as `--primary-text-color`,
  `--secondary-text-color` and `--card-background-color`. Avoid fixing light
  backgrounds or text colors. A user-selected bin color should accent an icon
  or border, with readable theme text retained beside it.
  [Theming and design tokens](https://contributors.home-assistant.io/frontend/architecture/theming/).
- **Accessibility:** use native buttons or HA controls for keyboard support,
  meaningful labels and visible focus. Status must include text or an icon,
  rather than color alone. Aim for 4.5:1 normal text contrast and generous touch
  targets; HA icon buttons default to 48 px. Check light/dark themes, keyboard,
  screen readers, reduced motion, 200% zoom and phone widths.
  [Accessibility guidance](https://contributors.home-assistant.io/design/foundations/accessibility/).
- **Locale and dates:** frontend date formatting uses `Intl.DateTimeFormat`
  with the HA language and resolved user/server time zone. Numeric formats also
  respect `locale.date_format`. Follow this behavior for timed values. Treat
  provider date-only collections as calendar dates: converting UTC midnight into
  a negative offset can move an all-day collection to the previous day. Compute
  countdowns using calendar-day values rather than elapsed 24-hour intervals
  across daylight-saving changes. The calendar-day recommendation is an
  implementation inference from the frontend's explicit date-only handling.
  [Frontend date formatter](https://github.com/home-assistant/frontend/blob/dev/src/common/datetime/format_date.ts),
  [calendar locale and timezone configuration](https://github.com/home-assistant/frontend/blob/dev/src/panels/calendar/ha-full-calendar.ts).

## Existing community cards

| Project | Verified behavior and useful ideas | License / limitations |
| --- | --- | --- |
| [TrashCard](https://github.com/idaho/hassio-trash-card) | Calendar events; editable text, icons, colors and pictures; multiple calendar entities; compact chips, icons and full cards; optional event grouping and filters. | [Apache 2.0](https://github.com/idaho/hassio-trash-card/blob/main/LICENSE). Calendar model and configured patterns differ from WCS sensor attributes. Its README contains a five-category restriction, so do not assume unlimited categories from its prose. |
| [Garbage Collection Card](https://github.com/amaximus/garbage-collection-card) | Sensor display with date/countdown and due-day colors. Explicit WCS support requires `details_format: generic` and a `value.daysTo` state template. | [MIT](https://github.com/amaximus/garbage-collection-card/blob/master/LICENSE). README announces support ending after February 2026; useful historical reference, not a maintained scaffold. The AnthonMS URL found during discovery was a 404; the verified owner is amaximus. |
| [Daire's waste card](https://github.com/dairefinn/daires-hass-cards.waste-card) | Multiple bins with per-bin entity, label, icon and accent. Reads ISO date attribute keys, selects the next future date and highlights the next bin. | [MIT](https://github.com/dairefinn/daires-hass-cards.waste-card/blob/main/LICENSE). Documented contract covers one WCS attribute format; do not assume it covers all configurable WCS sensor formats. |

## Image research

These are reference images linked by the original projects or their authors,
not assets copied into this integration:

- [TrashCard full-card layout](https://github.com/idaho/hassio-trash-card/assets/664101/f3f3130c-172f-42dc-aaca-2bc0c9a3bc26).
- [TrashCard using custom pictures](https://github.com/user-attachments/assets/3edb54f2-7232-4d20-8b48-bc947e7abddc).
- [Daire's multiple-bin screenshot](https://github.com/user-attachments/assets/97667d8b-a035-47e2-84f9-e53ae294632c).
- [Garbage Collection Card screenshot](https://raw.githubusercontent.com/amaximus/garbage-collection-card/master/garbage_collection_lovelace.jpg).
- [Community ReCollect card thread with screenshots and configurations](https://community.home-assistant.io/t/waste-collection-card-using-recollect/266410).

Search results included expiring signed image URLs; stable project/attachment
links are recorded here instead. Treat screenshots as inspiration. Use built-in
HA icons and optional user-supplied pictures for runtime cards; this avoids a
third-party image dependency and country-specific bin illustrations.

## Proposed card family

1. **Next collection:** a focused countdown and date, including every collection
   sharing the next day rather than silently choosing only one.
2. **Bins overview:** the next date for each configured waste type/entity, with
   optional labels, icons, pictures and accent colors.
3. **Upcoming collections:** a chronological agenda with configurable horizon,
   item count and grouping.

Use one shared adapter for actual WCS entity attributes and/or calendar events;
do not parse user-formatted display strings as the primary data contract.
Preserve provider labels in every language, permit arbitrary waste categories
and multiple sources, and impose no country-specific color or weekday rules.
Translate the card UI separately from upstream waste labels. Date and relative
day formatting should use HA locale preferences, including RTL layouts where
appropriate. Customization must remain available in the visual editor as well
as YAML.

Validation should include multiple simultaneous waste types, mixed sources,
empty data, unavailable/missing entities, long and non-Latin names, regional
date orders, negative/positive UTC offsets and DST boundaries. Verify the built
bundle, editor, picker, keyboard focus and layouts in the actual Waste
Collection Dashboard after deployment; a standalone preview cannot establish
live HA compatibility.
