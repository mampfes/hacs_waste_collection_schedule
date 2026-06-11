# City of Bayswater

Support for schedules provided by [City of Bayswater](https://www.bayswater.wa.gov.au/bins).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bayswater_wa_gov_au
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
    - name: bayswater_wa_gov_au
      args:
        address: 9 Wholley St Bayswater
```

## How to get the source arguments

Visit the [City of Bayswater bins page](https://www.bayswater.wa.gov.au/bins) and search for your address. The address should match the format used in the lookup, e.g. "9 Wholley St Bayswater".
