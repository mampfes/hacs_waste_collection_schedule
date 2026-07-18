# Launceston City Council

Support for schedules provided by [Launceston City Council](https://www.launceston.tas.gov.au).

Source for Launceston City Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: launceston_tas_gov_au
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
    - name: launceston_tas_gov_au
      args:
        address: 40 Southgate Dr, Kings Meadows, TAS
```

## How to get the source arguments

Enter your street address, e.g. '40 Southgate Dr, Kings Meadows, TAS'.
