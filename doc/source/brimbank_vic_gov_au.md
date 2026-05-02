# Brimbank City Council

Support for schedules provided by [Brimbank City Council](https://www.brimbank.vic.gov.au).

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
*(string) (required)* Your collection day: Monday, Tuesday, Wednesday, Thursday, or Friday.

**calendar**  
*(string) (required)* Your calendar cycle: A or B.

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

Download the [Brimbank Waste Calendar PDF](https://serviceapi.brimbank.vic.gov.au/CMServiceAPI/Record/7854806/file/document) and check the map on the back page. Find your street on the map to determine your collection **day** (Monday to Friday) and **calendar** cycle (A or B).
