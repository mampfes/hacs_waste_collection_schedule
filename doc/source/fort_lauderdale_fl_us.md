# Fort Lauderdale, FL

Support for schedules provided by [City of Fort Lauderdale, FL](https://www.fortlauderdale.gov/government/departments-i-z/public-works/operations/sanitation-operations/collection-programs).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fort_lauderdale_fl_us
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Full street address including city and state.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fort_lauderdale_fl_us
      args:
        address: 413 NW 15th Ave, Fort Lauderdale, FL 33311
```

## How to get the source arguments

Use your full street address including city, state and ZIP code. The source geocodes the address and queries the city's public "My Government Services" collection zones (https://gis.fortlauderdale.gov/MyGovernmentServices/) to determine your collection days.

Returned collection types:

- **Trash** - one or two days per week, depending on the zone.
- **Recycling** - weekly.
- **Bulk Trash** - monthly (e.g. 2nd Thursday).
- **Yard Waste** - weekly.

Note: Dates are derived from the zone's fixed weekly/monthly schedule and do not account for holiday shifts.
