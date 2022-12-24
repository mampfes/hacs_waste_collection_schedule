# Melton City Council

Support for schedules provided by [Melton City Council](https://www.melton.vic.gov.au/My-Area).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: melton_vic_gov_au
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
    - name: melton_vic_gov_au
      args:
        street_address: 23 PILBARA AVENUE BURNSIDE 3023
```

## How to get the source arguments

Visit the [Melton City Council waste and recycling](https://www.melton.vic.gov.au/My-Area) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.