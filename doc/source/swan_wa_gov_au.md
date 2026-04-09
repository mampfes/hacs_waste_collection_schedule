# City of Swan

Support for schedules provided by [City of Swan](https://www.swan.wa.gov.au/waste-and-sustainability/waste-and-recycling-services/bins/find-my-bin-day), Western Australia.

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
        address: "34 Oldenburg Pass Stratton"
```

## How to get the source arguments

Visit the [City of Swan Find My Bin Day](https://www.swan.wa.gov.au/waste-and-sustainability/waste-and-recycling-services/bins/find-my-bin-day) page and search for your address.
