# Moorabool Shire Council

Support for schedules provided by [Moorabool Shire Council](https://www.moorabool.vic.gov.au).

Source for Moorabool Shire Council rubbish collection.

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
        address: 139 Main Street Bacchus Marsh 3340
```

## How to get the source arguments

Go to <https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day> and make sure your address matches the auto-complete suggestions.
