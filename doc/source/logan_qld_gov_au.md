# Logan City Council

Support for schedules provided by [Logan City Council](https://www.logan.qld.gov.au).

Source for Logan City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: logan_qld_gov_au
      args:
        property_location: PROPERTY_LOCATION
```

### Configuration Variables

**property_location**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: logan_qld_gov_au
      args:
        property_location: 12 Ashton Street Kingston
```

## How to get the source arguments

Enter your street address as used on the Logan City Council MyLogan tool (https://www.logan.qld.gov.au/MyLogan), for example '12 Ashton Street Kingston'.
