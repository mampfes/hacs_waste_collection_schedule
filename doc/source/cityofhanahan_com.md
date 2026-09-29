# Hanahan, SC

Support for schedules provided by [Hanahan, SC](https://www.cityofhanahan.com/publicworks/page/household-trash-collection-schedule).

Regular curbside collection schedule for the City of Hanahan.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cityofhanahan_com
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cityofhanahan_com
      args:
        area: Hanahan Proper
```

## How to get the source arguments

The city publishes its collection days by named area, without an address lookup. Check the <a href="https://www.cityofhanahan.com/publicworks/page/household-trash-collection-schedule" target="_blank">household trash collection schedule</a> and select the area that serves your home. Spring Valley Mobile Home Park, Gold Cup Springs, North Rhett and Lakeview subdivision have their own household waste day; choose the Tuesday household waste area only for the streets and street segments the city lists under Tuesday. Holiday and emergency changes are not included.
