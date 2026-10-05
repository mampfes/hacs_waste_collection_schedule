# Seattle Public Utilities

Support for schedules provided by [Seattle Public Utilities](https://myutilities.seattle.gov).

Source for Seattle Public Utilities waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: seattle_gov
      args:
        street_address: STREET_ADDRESS
        prem_code: PREM_CODE
```

### Configuration Variables

**street_address**  
*(string) (required)*

**prem_code**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: seattle_gov
      args:
        street_address: 600 4th Ave
```

## How to get the source arguments

Enter the street address of the property, e.g. '600 4th Ave'. If the address lookup picks the wrong property, enter its premise code (the `premCode` the calendar lookup page at https://myutilities.seattle.gov/eportal/#/accountlookup/calendar receives for your address) as well.
