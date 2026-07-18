# Allerdale Borough Council

Support for schedules provided by [Allerdale Borough Council](https://www.allerdale.gov.uk).

Source for www.allerdale.gov.uk services for Allerdale Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: allerdale_gov_uk
      args:
        address_postcode: ADDRESS_POSTCODE
        address_name_number: ADDRESS_NAME_NUMBER
```

### Configuration Variables

**address_postcode**  
*(string) (required)*

**address_name_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: allerdale_gov_uk
      args:
        address_postcode: CA12 4HU
        address_name_number: '11'
```
