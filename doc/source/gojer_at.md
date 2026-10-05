# GOJER

Support for schedules provided by [GOJER](https://www.gojer.at/).

Source for GOJER.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gojer_at
      args:
        municipality: MUNICIPALITY
        city: CITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gojer_at
      args:
        municipality: Ruden
        city: Kleindiex
```

## How to get the source arguments

Select your municipality and town on https://www.gojer.at/service/abfuhrkalender.html and enter both names as shown there.
