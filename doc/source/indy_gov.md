# Indianapolis (Indy DPW / Marion County Solid Waste)

Support for trash, heavy trash and recycling pickup days in the [City of Indianapolis](https://www.indy.gov) (Marion County, Indiana, USA). The source covers every Indianapolis trash district, whether the Department of Public Works (DPW) or the contracted hauler LRS picks up.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: indy_gov
      args:
        address: ADDRESS
        recycling_date: RECYCLING_DATE  # optional
        include_heavy_trash: INCLUDE_HEAVY_TRASH  # optional
```

or, using coordinates instead of an address:

```yaml
waste_collection_schedule:
  sources:
    - name: indy_gov
      args:
        lat: LATITUDE
        lon: LONGITUDE
```

### Configuration Variables

**address**
_(String) (required unless `lat` and `lon` are set)_

Your Indianapolis street address, e.g. `200 E Washington St`. The source looks it up with the City's address locator (`gis.indy.gov`). If the locator can't match it closely enough, the error lists the nearest matches it found.

**lat** / **lon**
_(Float) (optional, set both, used instead of `address`)_

WGS84 latitude and longitude of your home. When both are set and `address` is empty, the source skips the address lookup.

**recycling_date**
_(String `YYYY-MM-DD`) (optional)_

Any one known recycling pickup date, past or future. Curbside recycling in Indianapolis is a paid subscription that LRS collects every other week. This date tells the source which weeks are recycling weeks. A date that was itself moved by a holiday also works, because only its week is used. **If you leave it out, no recycling pickups are shown.**

**include_heavy_trash**
_(Boolean) (optional, default `true`)_

Show the monthly heavy trash pickup, if your district has one on a fixed day each month.

## How to check your district

1. Open [Trash pickup](https://www.indy.gov/workflow/trash-pickup) on indy.gov and enter your address to see your trash day and heavy trash rule.
2. If you subscribe to recycling, check your recycling day at [Recycling](https://www.indy.gov/workflow/recycling). Use any pickup date from your LRS calendar or a past pickup as `recycling_date`.
3. The source uses the same city GIS data, so it should show the same trash day as indy.gov.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: indy_gov
      args:
        address: "200 E Washington St"
```

```yaml
waste_collection_schedule:
  sources:
    - name: indy_gov
      args:
        address: "40 E St Clair St"
        recycling_date: "2026-12-03"
```

```yaml
waste_collection_schedule:
  sources:
    - name: indy_gov
      args:
        lat: 39.650895
        lon: -86.1175485
        include_heavy_trash: false
```

## Waste types returned

| City data | Returned type | Icon |
|-----------|---------------|------|
| `DAY` (e.g. `THURSDAY`, `MON,THU`, `M,Tu,Th,F`) | Trash | `Icons.GENERAL_WASTE` |
| `HVYTRASHDA` = `<FIRST..FIFTH> <WEEKDAY> OF THE MONTH` | Heavy Trash | `Icons.BULKY` |
| `RC_DAY` = `EVERY OTHER <WEEKDAY>` (with `recycling_date`) | Recycling | `Icons.RECYCLING` |

## Limitations

- **Dates are worked out from district rules.** The City publishes each district's pickup day and rules, not a list of actual dates. This source builds about 10 weeks of dates from those rules.
- **Holiday slides are computed locally.** The source uses the 8 holidays on the City's "Holidays & Slide Schedules" list: New Year's Day, Martin Luther King Jr. Day, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving and Christmas. When one falls on a weekday, every pickup from the holiday through the end of that week moves one day later (Friday moves to Saturday). Holidays on a weekend cause no delay. Weather and other unplanned delays are not shown.
- **Recycling is a paid LRS subscription collected every other week.** Set `recycling_date` to see it.
- **Heavy trash only appears when the district has a fixed day each month**, such as "Fourth Thursday of the Month" in DPW districts. In LRS districts, you can put out 2 heavy items on any trash day, so no separate heavy trash date is shown. Other free-text rules are skipped too.
- **Beech Grove, Lawrence, Speedway and excluded areas are not served** by the City. For those addresses the source returns an error that names the town or hauler. Contact them directly.
- **Leaf season** (up to 40 bags a week picked up with regular trash) is not shown as a separate pickup.
- **LRS-hauled Indianapolis addresses:** use this source, not `lrsrecycles_com`. This one reads the City's district data and covers the City's holiday list.
- The source uses public ArcGIS services on `gis.indy.gov`. The City does not document them as an API, and they may change without notice.
