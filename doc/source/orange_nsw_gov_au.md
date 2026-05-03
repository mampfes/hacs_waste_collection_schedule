# Orange City Council

Support for waste collection schedules provided by [Orange City Council](https://www.orange.nsw.gov.au), NSW, Australia.

## Services Supported

| Collection Type | Bin Lid Colour | Frequency |
|---|---|---|
| General Waste | Red / Dark | Weekly (every Wednesday) |
| Recycling | Yellow | Fortnightly (Wednesday, Zone A or Zone B) |

> **Note:** Green waste is available as a paid additional service in Orange and is not included in the standard fortnightly bin collection calendar. See [orange.nsw.gov.au/waste](https://www.orange.nsw.gov.au/waste/) for details.

## Finding Your Zone

Orange City Council divides the city into two fortnightly recycling zones:

| Zone | Area |
|---|---|
| **Zone A** | Properties **west** of Anson Street |
| **Zone B** | Properties **east** of Anson Street; properties **on** Anson Street; and all properties in **Spring Hill**, **Lucknow**, and **Clifton Grove** |

If you are unsure of your zone, download the annual Waste Booklet from the [Orange City Council waste page](https://www.orange.nsw.gov.au/waste/) or contact Council on **+61 2 6393 8000**.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: orange_nsw_gov_au
      args:
        zone: A        # Use "A" or "B" — see table above
```

### Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `zone` | string | Yes | Your recycling collection zone: `"A"` (west of Anson St) or `"B"` (east of Anson St, Spring Hill, Lucknow, Clifton Grove) |

## Example Configurations

**Zone A** — e.g. 67 Molloy Drive, Orange NSW 2800 *(west of Anson Street)*:
```yaml
waste_collection_schedule:
  sources:
    - name: orange_nsw_gov_au
      args:
        zone: A
```

**Zone B** — e.g. Spring Hill or Lucknow:
```yaml
waste_collection_schedule:
  sources:
    - name: orange_nsw_gov_au
      args:
        zone: B
```

## Data Source & Annual Updates

Collection dates are hardcoded from the annual **Orange City Council Residential Waste Booklet** (PDF), published each year at:

📄 [https://www.orange.nsw.gov.au/waste/](https://www.orange.nsw.gov.au/waste/)

When a new year's booklet is published, the `_HARDCODED_SCHEDULES` dictionary in `orange_nsw_gov_au.py` should be updated with the new Zone A and Zone B recycling dates. The source will log a warning and fall back to an estimated fortnightly pattern if the current year's data is not present.

## How Collection Works

- **General Waste** (red/dark lid) is collected **every Wednesday** from the kerb.
- **Recycling** (yellow lid) is collected **every second Wednesday**, alternating between Zone A and Zone B. On your recycling week, put both bins out.
- Put bins out the **night before** (Tuesday evening) to ensure they are collected.

For further information visit the [Orange City Council waste page](https://www.orange.nsw.gov.au/waste/).
