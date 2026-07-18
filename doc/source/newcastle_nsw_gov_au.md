# City of Newcastle

Support for schedules provided by [City of Newcastle](https://www.newcastle.nsw.gov.au).

Source for City of Newcastle (NSW) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: newcastle_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: newcastle_nsw_gov_au
      args:
        address: 1 King Street, Newcastle NSW 2300
```

## How to get the source arguments

Enter your street address within the City of Newcastle (e.g. '1 King Street, Newcastle NSW 2300').
