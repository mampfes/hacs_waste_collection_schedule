# Lakeshore Recycling Systems (LRS)

Support for residential and commercial pickup days provided by [Lakeshore Recycling Systems (LRS)](https://www.lrsrecycles.com), serving communities in Illinois and Indiana, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lrsrecycles_com
      args:
        address: ADDRESS
        zip: ZIP
        recycling_date: RECYCLING_DATE  # optional
        include_commercial: INCLUDE_COMMERCIAL  # optional
        organics_start: ORGANICS_START  # optional
        organics_end: ORGANICS_END  # optional
```

### Configuration Variables

**address**
_(String) (required)_

House number and street line only, without city or state (e.g. `123 MADISON ST`). The address is upper-cased, whitespace is collapsed, trailing periods/commas are removed, and common words are abbreviated USPS-style (`STREET` → `ST`, `AVENUE` → `AVE`, `ROAD` → `RD`, `DRIVE` → `DR`, `LANE` → `LN`, `COURT` → `CT`, `BOULEVARD` → `BLVD`, `PLACE` → `PL`, `PARKWAY` → `PKWY`, `TERRACE` → `TER`, `CIRCLE` → `CIR`, `HIGHWAY` → `HWY`, `NORTH/SOUTH/EAST/WEST` → `N/S/E/W`). It must start with a house number.

**zip**
_(String or Integer) (required)_

5-digit ZIP code.

**recycling_date**
_(String `YYYY-MM-DD`) (optional)_

Any one known residential recycling pickup date (past or future). LRS collects residential recycling every other week; this date is used to work out which weeks are recycling weeks. A date that was itself moved by a holiday works too, because only its week is used. If omitted, residential recycling is shown **every week** (and a warning is logged).

**include_commercial**
_(Boolean) (optional, default `false`)_

Also show commercial (`COMML ...`) services for the address. If the address has no residential services at all, commercial services are shown automatically.

**organics_start** / **organics_end**
_(String `MM-DD`) (optional, set both or neither)_

First and last day of the organics (yard waste and/or food scrap compost) season, e.g. `04-01` and `11-30`. Organics pickups are only shown between these dates each year; a season that wraps around the new year (e.g. `11-01` to `02-28`) also works. If omitted, organics are shown **every week all year**, which is correct for towns with year-round compost carts. Your town's season is listed on its page at [lrsrecycles.com](https://www.lrsrecycles.com) (or on your town's website).

## How to find your address

1. Open the [LRS service map](https://www.lrsrecycles.com/map).
2. Use the **"Current Customer? Want to see your pickup day?"** form and enter your street line and ZIP code.
3. If LRS shows your pickup day, use the same street line (house number + street, USPS abbreviations, no city/state) as `address`.
4. Take any recycling pickup date you know (e.g. from your LRS calendar or a past pickup) as `recycling_date`.

The LRS lookup matches the address text as a substring, so `123 MADISON ST` works but `123 Madison Street, Oak Park IL` does not (this source already abbreviates `Street`, but city/state must be left out).

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: lrsrecycles_com
      args:
        address: "123 Madison Street"
        zip: "60302"
        recycling_date: "2026-12-03"
        organics_start: "04-01"
        organics_end: "11-30"
```

```yaml
waste_collection_schedule:
  sources:
    - name: lrsrecycles_com
      args:
        address: "850 Waukegan Rd"
        zip: "60015"
        include_commercial: true
```

## Waste types returned

| LRS service type | Returned type | Icon |
|------------------|---------------|------|
| `RESI TRASH`, `RESI TRASH BD` | Trash | `Icons.GENERAL_WASTE` |
| `RESI RECYCLE` (biweekly) | Recycling | `Icons.RECYCLING` |
| `RESI ORGANICS` | Organics | `Icons.ORGANIC` |
| `COMML * TRASH` | Commercial Trash | `Icons.GENERAL_WASTE` |
| `COMML * RECYCLE` | Commercial Recycling | `Icons.RECYCLING` |
| `COMML * ORGANICS` | Commercial Organics | `Icons.ORGANIC` |

`RESI ORGANICS` means different things depending on the town: yard waste only (e.g. Braidwood, roughly April–November), yard waste mixed with food scraps (e.g. Geneva, St. Charles), or a year-round compost cart (e.g. Northbrook). Check your town's LRS page for what is accepted.

Unknown service types are returned with their title-cased name and the general waste icon.

## Limitations

- **Holidays are computed locally.** LRS observes New Year's Day, Memorial Day, Independence Day, Labor Day, Thanksgiving and Christmas. When one of them falls on a weekday, every pickup from the holiday through the end of that week moves one day later. Holidays on a weekend cause no delay. LRS posts its service notices as free text that a program can't read, so other delays (e.g. weather) are not shown.
- **Biweekly recycling needs `recycling_date`.** Without it, residential recycling is shown weekly.
- **The organics season is not provided by LRS.** Set `organics_start`/`organics_end` yourself; without them organics are shown weekly all year.
- **Indianapolis residents should use the [`indy_gov`](./indy_gov.md) source instead.** In Indianapolis, LRS follows the City's schedule, which observes two extra holidays (MLK Jr. Day and Juneteenth) that this source does not apply, and the LRS lookup does not return every LRS-served Indianapolis address. The City source covers all City-served addresses, including LRS-hauled districts and LRS recycling.
- The source uses the lookup endpoint behind the LRS website. LRS does not document it, and it may change without notice.
