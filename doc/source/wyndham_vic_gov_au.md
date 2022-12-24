# Wyndham City Council

Support for schedules provided by [Wyndham City Council](https://digital.wyndham.vic.gov.au/myWyndham/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wyndham_vic_gov_au
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
    - name: wyndham_vic_gov_au
      args:
        street_address: 300 SAYERS ROAD TRUGANINA 3029
```

## How to get the source arguments

Visit the [Wyndham City Council waste and recycling](https://digital.wyndham.vic.gov.au/myWyndham/) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.