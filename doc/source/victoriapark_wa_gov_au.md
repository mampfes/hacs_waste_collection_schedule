# Town of Victoria Park

Support for schedules provided by [Town of Victoria Park Bins and Collections](https://www.victoriapark.wa.gov.au/residents/waste-and-recycling/bins-and-collections.aspx).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: victoriapark_wa_gov_au
      args:
        group: GROUP
        day: DAY
```

### Configuration Variables

**group**  
*(int) (required)* Collection group: `1` or `2`

**day**  
*(string) (required)* Collection day: `Monday`, `Tuesday`, `Wednesday`, `Thursday`, or `Friday`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: victoriapark_wa_gov_au
      args:
        group: 1
        day: Monday
```

## How to get the source arguments

Visit the [Bins and Collections](https://www.victoriapark.wa.gov.au/residents/waste-and-recycling/bins-and-collections.aspx) page to find your collection group (1 or 2) and collection day from the calendar images.

Collection types:

- **FOGO** (Food Organics/Garden Organics) — collected weekly
- **Recycling** — collected fortnightly (yellow weeks)
- **General Waste** — collected fortnightly (red weeks)
