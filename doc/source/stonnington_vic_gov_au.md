# Stonnington City Council

Support for schedules provided by [Stonnington City Council](https://www.stonnington.vic.gov.au/Services/Waste-and-recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stonnington_vic_gov_au
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
    - name: stonnington_vic_gov_au
      args:
        street_address: 500 Chapel Street, South Yarra
```

## How to get the source arguments

Visit the [Stonnington City Council waste and recycling](https://www.stonnington.vic.gov.au/Services/Waste-and-recycling) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
