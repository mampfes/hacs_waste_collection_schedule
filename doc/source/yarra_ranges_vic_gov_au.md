# Yarra Ranges Council

Support for schedules provided by [Yarra Ranges Council](https://www.yarraranges.vic.gov.au).

Source for Yarra Ranges Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: yarra_ranges_vic_gov_au
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
    - name: yarra_ranges_vic_gov_au
      args:
        street_address: 5/447-449 Maroondah Highway Lilydale 3140
```

## How to get the source arguments

Enter your full street address as it appears on the council's waste collection lookup page (street, suburb and postcode).
