# Cheltenham Borough Council

Support for schedules provided by [Cheltenham Borough Council](https://www.cheltenham.gov.uk).

Source for Cheltenham Borough Council waste collection schedule

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cheltenham_gov_uk
      args:
        property_id: PROPERTY_ID
```

### Configuration Variables

**property_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cheltenham_gov_uk
      args:
        property_id: 55297
```

## How to get the source arguments

Visit https://cheltenham-host01.oncreate.app/w/webpage/collection-lookup, enter your postcode, select your address, then note the numeric property ID shown in the page.
