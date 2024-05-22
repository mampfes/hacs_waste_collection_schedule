# City of Ballarat

Support for schedules provided by [City of Ballarat](https://data.ballarat.vic.gov.au/pages/waste-collection-day/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ballarat_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ballarat_vic_gov_au
      args:
        street_address: 202 Humffray Street South BAKERY HILL VIC 3350
```

## How to get the source arguments

Visit the [City of Ballarat waste collection calendar](https://data.ballarat.vic.gov.au/pages/waste-collection-day/) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
