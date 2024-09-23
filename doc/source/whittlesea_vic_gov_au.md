# City of Whittlesea Council

Support for schedules provided by [City of Whittlesea Council](https://www.whittlesea.vic.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: whittlesea_vic_gov_au
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
    - name: whittlesea_vic_gov_au
      args:
        street_address: 25 Ferres Boulevard, South Morang 3752
```

## How to get the source arguments

Visit the [City of Whittlesea Council My Neighbourhood](https://www.whittlesea.vic.gov.au/My-Neighbourhood) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
