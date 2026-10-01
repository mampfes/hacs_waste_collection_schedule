# Mole Valley District Council

Support for schedules provided by [Mole Valley District Council](https://www.molevalley.gov.uk).

Source for molevalley.gov.uk services for Mole Valley District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mole_valley_gov_uk
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
    - name: mole_valley_gov_uk
      args:
        postcode: RH4 1BT
        house_number: '44'
```

## How to get the source arguments

Enter your postcode and house number or name (e.g. 17 or Rose Cottage). You can verify your address at https://myproperty.molevalley.gov.uk/molevalley/
