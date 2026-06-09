# Moorabool Shire Council

Support for schedules provided by [Moorabool Shire Council Waste and Recycling](https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moorabool_vic_gov_au
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
    - name: moorabool_vic_gov_au
      args:
        address: "139 Main Street Bacchus Marsh 3340"
```

## How to get the source arguments

Visit the [Moorabool Shire Council bin collection day](https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day) page and search for your address. The address arguments used to configure hacs_waste_collection_schedule should exactly match the address shown in the autocomplete result.
