# Tandridge District Council

Support for schedules provided by [Tandridge District Council](https://www.tandridge.gov.uk).

Source for Tandridge District Council, UK, waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tandridge_gov_uk
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**postcode**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tandridge_gov_uk
      args:
        postcode: RH8 0PG
        house_number: 14A
```

## How to get the source arguments

Enter your postcode and your house number/name exactly as it appears when you look up your address at https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/tfaBranded/408 (e.g. '14A').
