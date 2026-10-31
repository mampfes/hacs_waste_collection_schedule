# Rossendale Borough Council

Support for schedules provided by [Rossendale Borough Council](https://www.rossendale.gov.uk).

Source for Rossendale Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rossendale_gov_uk
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
    - name: rossendale_gov_uk
      args:
        postcode: OL12 8PJ
        house_number: '13'
```

## How to get the source arguments

Enter your postcode and your house number (or house name, as listed at https://www.rossendale.gov.uk/directory/10094/bin-collection-days).
