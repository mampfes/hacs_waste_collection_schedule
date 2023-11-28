# Lancaster City Council

Support for schedules provided by [Lancaster City Council](https://www.lancaster.gov.uk/bins-recycling), serving the
city of Lancaster, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lancaster_gov_uk
      args:
        house_number: HOUSE NUMBER OR NAME
        postcode: POSTCODE
```

### Configuration Variables

**postcode**
*(string) (required)*

**house_number**
*(int or string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lancaster_gov_uk
      args:
        house_number: 1
        postcode: LA1 1RS
```

## Exported Bins

  - Domestic Waste
  - Garden Waste
  - Recycling
