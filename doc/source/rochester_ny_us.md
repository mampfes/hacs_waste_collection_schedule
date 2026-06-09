# Rochester, NY

Support for schedules provided by [Rochester, NY](https://www.cityofrochester.gov/departments/department-environmental-services/refuse-and-recycling-collection-schedule).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rochester_ny_us
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rochester_ny_us
      args:
        address: 124 Parsells Ave, Rochester, NY
```

## How to get the source arguments

Visit the [Rochester Service Locator](http://maps.cityofrochester.gov/ServiceLocator/) and search for your address. Use your full street address including city and state (e.g. "124 Parsells Ave, Rochester, NY").
