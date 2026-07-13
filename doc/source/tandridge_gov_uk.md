# Tandridge District Council

Support for schedules provided by [Tandridge District
Council](https://www.tandridge.gov.uk), serving the Tandridge District, Surrey, UK.

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
        postcode: "RH8 0PG"
        house_number: "14A"
```

## How to get the source arguments

1. Go to <https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/tfaBranded/408>, enter your postcode, and select your address from the dropdown.
2. Your postcode is the first argument.
3. Your house number/name is the second argument — use it exactly as it appears at the start of your address in the dropdown (e.g. `14A`).
