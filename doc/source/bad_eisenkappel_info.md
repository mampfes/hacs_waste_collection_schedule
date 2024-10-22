# Eisenkappel-Vellach / Bad Eisenkappel

Support for schedules provided by [Bad Eisenkappel](https://www.bad-eisenkappel.info/), serving Eisenkappel-Vellach, Germany.

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
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: bad_eisenkappel_info
      args:
        region: Leppen
```

## How to get the source argument

The region should match one of the regions listed in the third column of the table at <https://www.bad-eisenkappel.info/gemeinde/onlineservice/abfuhrtermine.html>