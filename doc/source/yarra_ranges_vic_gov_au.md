# Yarra Ranges Council

Support for schedules provided by [Yarra Ranges Council](https://www.yarraranges.vic.gov.au/Environment/Waste/Find-your-waste-collection-and-burning-off-dates).

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
        street_address: 316 Maroondah Hwy, Healesville VIC 3777
```

## How to get the source arguments

Visit the [Yarra Ranges Council](https://www.yarraranges.vic.gov.au/Environment/Waste/Find-your-waste-collection-and-burning-off-dates) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
