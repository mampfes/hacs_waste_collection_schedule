# Gold Coast City Council

Support for schedules provided by [Gold Coast City Council](https://www.goldcoast.qld.gov.au/Services/Waste-recycling/Find-my-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: goldcoast_qld_gov_au
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
    - name: goldcoast_qld_gov_au
      args:
        street_address: 6/8 Henchman Ave Miami
```

## How to get the source arguments

The Gold Coast API allows for a fuzzy search, so no need to get overly complicated with the address. However, you can visit the [Gold Coast City Council](https://www.goldcoast.qld.gov.au/Services/Waste-recycling/Find-my-bin-day) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
