# Brimbank City Council

Support for schedules provided by [Brimbank City Council](https://www.brimbank.vic.gov.au).

Source for Brimbank City Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: brimbank_vic_gov_au
      args:
        day: DAY
        calendar: CALENDAR
```

### Configuration Variables

**day**  
*(string) (required)*

**calendar**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: brimbank_vic_gov_au
      args:
        day: Monday
        calendar: A
```

## How to get the source arguments

Your collection day (Monday to Friday) and calendar cycle (A or B) are shown on the map on the back of the council's waste calendar PDF (linked from https://www.brimbank.vic.gov.au/living-here/my-home/rubbish-recycling-and-other-waste/bins).
