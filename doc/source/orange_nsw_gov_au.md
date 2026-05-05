# Orange City Council

Support for waste collection schedules provided by [Orange City Council](https://www.orange.nsw.gov.au), NSW, Australia.

## Services Supported

| Collection Type | Bin Lid Colour | Frequency |
|---|---|---|
| General Waste | Red / Dark | Weekly (every Wednesday) |
| Recycling | Yellow | Fortnightly (Wednesday, Zone A or Zone B) |

## Finding Your Zone

Orange City Council divides the city into two fortnightly recycling zones (referred to in the waste booklet as **Week A** and **Week B**):

| Zone | Area |
|---|---|
| **Zone A** | Properties **west** of Anson Street |
| **Zone B** | Properties **east** of Anson Street; properties **on** Anson Street; and all properties in **Spring Hill**, **Lucknow**, and **Clifton Grove** |

Download the annual Waste Booklet from the [Orange City Council waste page](https://www.orange.nsw.gov.au/waste/) to confirm your zone, or contact Council on **+61 2 6393 8000**.

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

## How It Works

Collection dates are calculated mathematically from the fortnightly Wednesday pattern — no annual updates are required. At runtime the source fetches the council's waste page to locate the current booklet PDF URL and extract the schedule year, ensuring the correct calendar year is always used. If the council website is unreachable, the source falls back to the current calendar year with a warning logged.

## How Collection Works

- **General Waste** (red/dark lid) is collected **every Wednesday** from the kerb.
- **Recycling** (yellow lid) is collected **every second Wednesday**, alternating between Zone A and Zone B.
- Put bins out the **night before** (Tuesday evening) to ensure they are collected.

For further information visit the [Orange City Council waste page](https://www.orange.nsw.gov.au/waste/).
