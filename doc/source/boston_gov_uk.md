# Boston Borough Council

Support for schedules provided by [Boston Borough Council](https://www.boston.gov.uk).

Source for www.boston.gov.uk services for Boston Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: boston_gov_uk
      args:
        postcode: POSTCODE
        property: PROPERTY
```

### Configuration Variables

**postcode**  
*(string) (required)*

**property**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: boston_gov_uk
      args:
        postcode: PE20 3LW
        property: '43'
```

## How to get the source arguments

Enter your postcode and property name or number as they appear on the Boston Borough Council website: https://www.boston.gov.uk/article/27449/Your-Waste-Collections
