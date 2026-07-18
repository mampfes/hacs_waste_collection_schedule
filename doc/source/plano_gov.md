# City of Plano

Support for schedules provided by [City of Plano](https://www.plano.gov/630/Residential-Collection-Schedules).

Source script for plano.gov

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: plano_gov
      args:
        objectId: OBJECTID
        daysToGenerate: DAYSTOGENERATE
```

### Configuration Variables

**objectId**  
*(string) (required)*

**daysToGenerate**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: plano_gov
      args:
        objectId: '72866'
        daysToGenerate: '3'
```

## How to get the source arguments

Use the Plano interactive waste map (https://www.plano.gov/630/Residential-Collection-Schedules) to search for and retrieve your object ID using browser dev tools or a capture tool like Fiddler.
