# City of Ballarat

Support for schedules provided by [City of Ballarat](https://www.ballarat.vic.gov.au).

Source for City of Ballarat rubbish collection.

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

Check your address on https://data.ballarat.vic.gov.au/pages/waste-collection-day/ and enter it as it is listed there.
