# Lancaster City Council

Support for schedules provided by [Lancaster City Council](https://lancaster.gov.uk).

Source for lancaster.gov.uk services for Lancaster City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lancaster_gov_uk
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**postcode**  
*(string) (required)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lancaster_gov_uk
      args:
        house_number: 1
        postcode: LA1 1RS
```

## How to get the source arguments

Provide your postcode and house name or number as shown on the council's bin-day lookup.
