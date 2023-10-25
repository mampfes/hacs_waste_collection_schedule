# Cederbaum Braunschweig

Support for paper waste collection schedules provided by [Cederbaum Container GmbH](https://www.cederbaum.de/), serving the city of Braunschweig, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cederbaum_de
      args:
        street: STREET
```

### Configuration Variables

**street**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: cederbaum_de
      args:
        street: "Hans-Sommer-Str."
```

## How to get the source argument

Find the parameter of your street using [https://www.cederbaum.de/blaue-tonne/abfuhrkalender](https://www.cederbaum.de/blaue-tonne/abfuhrkalender) and write them exactly like on the web page.
