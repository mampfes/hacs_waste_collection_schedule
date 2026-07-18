# City of Swan

Support for schedules provided by [City of Swan](https://www.swan.wa.gov.au).

Source for City of Swan waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: swan_wa_gov_au
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
    - name: swan_wa_gov_au
      args:
        address: 34 Oldenburg Pass Stratton
```

## How to get the source arguments

Enter your street address including suburb (e.g. '34 Oldenburg Pass Stratton'). Search at https://www.swan.wa.gov.au/waste-and-sustainability/waste-and-recycling-services/bins/find-my-bin-day
