# Bolton Council

Support for schedules provided by [Bolton Council](https://www.bolton.gov.uk).

Source for Bolton Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bolton_gov_uk
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
    - name: bolton_gov_uk
      args:
        postcode: BL52AX
        house_number: '13'
```

## How to get the source arguments

Enter your postcode and the start of your address as the council's address list shows it (the house number, or a house name).
