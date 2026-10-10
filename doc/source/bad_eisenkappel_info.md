# Eisenkappel-Vellach

Support for schedules provided by [Eisenkappel-Vellach](https://www.bad-eisenkappel.info/).

Source for Eisenkappel-Vellach.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bad_eisenkappel_info
      args:
        region: REGION
```

### Configuration Variables

**region**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bad_eisenkappel_info
      args:
        region: Leppen
```

## How to get the source arguments

The region should match one of the regions listed in the third column of the table at <https://www.bad-eisenkappel.info/gemeinde/onlineservice/abfuhrtermine.html>
